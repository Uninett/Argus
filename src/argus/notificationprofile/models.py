from __future__ import annotations

from datetime import datetime, time
import logging
from typing import TYPE_CHECKING, Dict, Optional

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from argus.auth.models import User

if TYPE_CHECKING:
    from argus.incident.models import Event, Incident  # noqa: F401

TriState = Optional[bool]

LOG = logging.getLogger(__name__)


class Timeslot(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="timeslots")
    name = models.CharField(max_length=40)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "user"], name="%(class)s_unique_name_per_user")]
        ordering = ["name"]

    def __str__(self):
        return self.name

    def timestamp_is_within_time_recurrences(self, timestamp: datetime):
        for time_recurrence in self.time_recurrences.all():
            if time_recurrence.timestamp_is_within(timestamp):
                return True
        return False


class TimeRecurrence(models.Model):
    class Day(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    DAY_START = time.min
    DAY_END = time.max

    timeslot = models.ForeignKey(to=Timeslot, on_delete=models.CASCADE, related_name="time_recurrences")

    days = ArrayField(base_field=models.IntegerField(choices=Day.choices), size=7)
    start = models.TimeField(help_text="Local time.")
    end = models.TimeField(help_text="Local time.")

    # TODO: is this method needed?
    """
    def __eq__(self, other):
        if type(other) is not TimeRecurrence:
            return False
        if super().__eq__(other):
            return True
        return (
                self.isoweekdays == other.isoweekdays
                and self.start == other.start
                and self.end == other.end
        )
    """

    def __str__(self):
        days = self.get_days_list()
        return f"{self.start}-{self.end} on {days}"

    @property
    def isoweekdays(self):
        # `days` are stored as strings in the db
        return {int(day) for day in self.days}

    def get_days_list(self):
        return [self.Day(day).label for day in self.days]

    def timestamp_is_within(self, timestamp: datetime):
        # FIXME: Might affect performance negatively if calling this method frequently
        timestamp = timestamp.astimezone(timezone.get_current_timezone())
        return timestamp.isoweekday() in self.isoweekdays and self.start <= timestamp.time() <= self.end

    def save(self, *args, **kwargs):
        # Ensure that the days are always sorted, for a nicer display
        if self.days:
            self.days = sorted(self.days)
        super().save(*args, **kwargs)


class Filter(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="filters")
    name = models.CharField(max_length=40)
    filter = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "user"], name="%(class)s_unique_name_per_user")]

    def __str__(self):
        return f"{self.name} [{self.filter}]"


class Media(models.Model):
    class Meta:
        verbose_name = "Medium"
        verbose_name_plural = "Media"

    MEDIA_NAME_LENGTH = 20
    slug = models.SlugField(max_length=MEDIA_NAME_LENGTH, blank=True, primary_key=True)
    name = models.CharField(max_length=MEDIA_NAME_LENGTH)
    installed = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.slug}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Media, self).save(*args, **kwargs)


class DestinationConfig(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "settings"], name="unique_destination_per_user"),
            models.UniqueConstraint(fields=["user", "media", "label"], name="unique_label_per_user_and_medium"),
        ]

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="destinations")
    media = models.ForeignKey(
        to=Media,
        on_delete=models.CASCADE,
        related_name="destinations",
    )
    label = models.CharField(max_length=50, blank=True, null=True)
    settings = models.JSONField()

    def __str__(self):
        if self.label:
            return self.label
        return f"{self.media.name}: {list(self.settings.values())}"


class NotificationProfile(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_name_per_user"),
        ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="notification_profiles")
    timeslot = models.ForeignKey(
        to=Timeslot,
        on_delete=models.CASCADE,
        related_name="notification_profiles",
    )
    filters = models.ManyToManyField(to=Filter, related_name="notification_profiles")
    name = models.CharField(
        max_length=40,
        blank=True,
        null=True,
    )
    active = models.BooleanField(default=True)
    destinations = models.ManyToManyField(
        to=DestinationConfig,
        related_name="notification_profiles",
        blank=True,
    )

    def __str__(self):
        if self.name:
            return f"{self.name}"
        return f"{self.timeslot}: {', '.join(str(f) for f in self.filters.all())}"
