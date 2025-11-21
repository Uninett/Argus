from __future__ import annotations

import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.utils import timezone

from argus.filter.filterwrapper import FilterWrapper
from argus.incident.models import Incident
from argus.notificationprofile.models import Filter
from argus.util.datetime_utils import INFINITY, INFINITY_REPR


LOG = logging.getLogger(__name__)
User = get_user_model()

MODIFICATION_WINDOW_PM = timedelta(hours=12)


class PlannedMaintenanceTask(models.Model):
    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(end_time__gt=F("start_time")),
                name="end_time_after_start_time",
                violation_error_message="End_time needs to be after start_time",
            ),
        ]

    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="planned_maintenance_tasks")
    created = models.DateTimeField(default=timezone.now, blank=True)
    start_time = models.DateTimeField(default=timezone.now, blank=True)
    end_time = models.DateTimeField(default=INFINITY, blank=True, null=True)
    description = models.CharField(blank=True, max_length=255)
    filters = models.ManyToManyField(to=Filter, related_name="planned_maintenance_tasks", blank=True)

    @property
    def modifiable(self) -> bool:
        return self.end_time == INFINITY or timezone.now() < self.end_time + MODIFICATION_WINDOW_PM

    def covers_incident(self, incident: Incident) -> bool:
        if self.start_time > incident.end_time or self.end_time < incident.start_time:
            return False
        return any(FilterWrapper(f.filter).incident_fits(incident) for f in self.filters.only("filter"))

    def __str__(self):
        return f"Planned maintenance from {self.start_time} to {self.end_time if self.end_time != INFINITY else INFINITY_REPR} owned by {self.owner} - {self.description}"
