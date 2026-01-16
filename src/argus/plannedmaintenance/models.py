from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.utils import timezone

from argus.notificationprofile.models import Filter
from argus.util.datetime_utils import LOCAL_INFINITY, INFINITY_REPR


LOG = logging.getLogger(__name__)
User = get_user_model()

MODIFICATION_WINDOW_PM = timedelta(hours=12)


class PlannedMaintenanceQuerySet(models.QuerySet):
    def future(self):
        return self.filter(start_time__gt=timezone.now())

    def past(self):
        return self.filter(end_time__lt=timezone.now())

    def current(self):
        return self.active_at_time(timezone.now())

    def active_at_time(self, time: Optional[datetime] = None):
        if not time:
            time = timezone.now()
        return self.filter(start_time__lte=time, end_time__gte=time)


class PlannedMaintenanceTask(models.Model):
    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="end_time_after_start_time",
                violation_error_message="End_time needs to be after start_time",
            ),
        ]

    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="planned_maintenance_tasks")
    created = models.DateTimeField(default=timezone.now)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=LOCAL_INFINITY)
    description = models.CharField(blank=True, max_length=255)
    filters = models.ManyToManyField(to=Filter, related_name="planned_maintenance_tasks")

    objects = PlannedMaintenanceQuerySet.as_manager()

    @property
    def modifiable(self) -> bool:
        return self.end_time > timezone.now() - MODIFICATION_WINDOW_PM

    @property
    def current(self):
        return self.active_at_time(timezone.now())

    def active_at_time(self, time: Optional[datetime] = None):
        if not time:
            time = timezone.now()
        return self.start_time <= time <= self.end_time

    def cancel(self, end_time: Optional[datetime] = None):
        """
        Sets the end time to the given time, if it is before the current end time

        If the start time is later than the given time, delete the task instead
        """
        if not end_time:
            end_time = timezone.now()

        if self.end_time <= end_time:
            return

        if self.start_time > end_time:
            self.delete()
            return

        self.end_time = end_time
        self.save()

    def clean(self):
        super().clean()
        if self.pk is not None:
            old = type(self).objects.get(pk=self.pk)
            if not old.modifiable:
                raise ValidationError(
                    "This planned maintenance task is no longer modifiable as it ended more than 12 hours ago."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Planned maintenance from {self.start_time} to {self.end_time if self.end_time != LOCAL_INFINITY else INFINITY_REPR} created by {self.created_by} - {self.description}"
