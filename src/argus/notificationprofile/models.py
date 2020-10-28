from __future__ import annotations

import json
from datetime import datetime, time
from functools import reduce
from operator import or_
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from multiselectfield import MultiSelectField

from argus.auth.models import User

if TYPE_CHECKING:
    from argus.incident.models import Incident


class Timeslot(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="timeslots")
    name = models.CharField(max_length=40)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "user"], name="%(class)s_unique_name_per_user"),
        ]
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

    days = MultiSelectField(choices=Day.choices, min_choices=1)
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
        days_string = ", ".join(f"{day}s" for day in self.get_days_list())
        return f"{self.start}-{self.end} on {days_string}"

    @property
    def isoweekdays(self):
        # `days` are stored as strings in the db
        return {int(day) for day in self.days}

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
    FILTER_NAMES = set(("sourceSystemIds", "tags"))
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="filters")
    name = models.CharField(max_length=40)
    filter_string = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "user"], name="%(class)s_unique_name_per_user"),
        ]

    def __str__(self):
        return f"{self.name} [{self.filter_string}]"

    @property
    def filter_json(self):
        return json.loads(self.filter_string)

    @property
    def all_incidents(self):
        # Prevent cyclical import
        from argus.incident.models import Incident

        return Incident.objects.all()

    @property
    def filtered_incidents(self):
        data = self.filter_json
        filtered_by_source = self.incidents_with_source_systems(data)
        filtered_by_tags = self.incidents_with_tags(data)
        return filtered_by_source & filtered_by_tags

    def incidents_with_source_systems(self, data=None):
        if not data:
            data = self.filter_json
        source_list = data.pop("sourceSystemIds", [])
        if source_list:
            return self.all_incidents.filter(source__in=source_list)
        return self.all_incidents

    def source_system_fits(self, incident: Incident, data=None):
        if not data:
            data = self.filter_json
        return self.incidents_with_source_systems(data).filter(id=incident.id).exists()

    def incidents_with_tags(self, data=None):
        if not data:
            data = self.filter_json
        tags_list = data.pop("tags", [])
        if tags_list:
            return self.all_incidents.from_tags(*tags_list)
        return self.all_incidents

    def tags_fit(self, incident: Incident, data=None):
        if not data:
            data = self.filter_json
        return self.incidents_with_tags(data).filter(id=incident.id).exists()

    def incident_fits(self, incident: Incident):
        data = self.filter_json
        source_fits = self.source_system_fits(incident, data)
        tags_fit = self.tags_fit(incident, data)
        return source_fits and tags_fit


class NotificationProfile(models.Model):
    class Media(models.TextChoices):
        EMAIL = "EM", "Email"
        SMS = "SM", "SMS"

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="notification_profiles")
    timeslot = models.OneToOneField(
        to=Timeslot,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="notification_profile",
    )
    filters = models.ManyToManyField(to=Filter, related_name="notification_profiles")

    # TODO: support for multiple email addresses / phone numbers / etc.
    media = MultiSelectField(choices=Media.choices, min_choices=1, default=[Media.EMAIL])
    active = models.BooleanField(default=True)
    phone_number = models.ForeignKey("argus_auth.PhoneNumber", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.timeslot}: {', '.join(str(f) for f in self.filters.all())}"

    @property
    def filtered_incidents(self):
        qs = [filter_.filtered_incidents for filter_ in self.filters.all()]
        return reduce(or_, qs)

    def incident_fits(self, incident: Incident):
        if not self.active:
            return False
        return self.timeslot.timestamp_is_within_time_recurrences(incident.start_time) and any(
            f.incident_fits(incident) for f in self.filters.all()
        )
