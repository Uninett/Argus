from __future__ import annotations

from datetime import datetime, time
from functools import reduce
import logging
from operator import or_
from typing import TYPE_CHECKING, Dict, Optional

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from argus.auth.models import User
from argus.filter.filterwrapper import FilterWrapper
from argus.filter.constants import DEPRECATED_FILTER_NAMES

if TYPE_CHECKING:
    from argus.incident.models import Event, Incident

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
    FILTER_NAMES = set(DEPRECATED_FILTER_NAMES)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="filters")
    name = models.CharField(max_length=40)
    filter = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "user"], name="%(class)s_unique_name_per_user")]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_wrapper = FilterWrapper(self.filter)

    def __str__(self):
        return f"{self.name} [{self.filter}]"

    @property
    def is_empty(self):
        return self.filter_wrapper.is_empty

    @property
    def all_incidents(self):
        # Prevent cyclical import
        from argus.incident.models import Incident

        return Incident.objects.all()

    # XXX wrong location
    @property
    def filtered_incidents(self):
        if self.is_empty:
            return self.all_incidents.none().distinct()
        data = self.filter
        filtered_by_source = self.incidents_with_source_systems(data=data)
        filtered_by_tags = self.incidents_with_tags(data=data)
        filtered_by_tristates = self.incidents_fitting_tristates(data=data)
        filtered_by_maxlevel = self.incidents_fitting_maxlevel(data=data)

        return filtered_by_source & filtered_by_tags & filtered_by_tristates & filtered_by_maxlevel

    # XXX wrong location
    def incidents_with_source_systems(self, data=None):
        if not data:
            data = self.filter.copy()
        source_list = data.pop("sourceSystemIds", [])
        if source_list:
            return self.all_incidents.filter(source__in=source_list).distinct()
        return self.all_incidents.distinct()

    # XXX wrong location
    def incidents_with_tags(self, data=None):
        if not data:
            data = self.filter.copy()
        tags_list = data.pop("tags", [])
        if tags_list:
            return self.all_incidents.from_tags(*tags_list)
        return self.all_incidents.distinct()

    # XXX wrong location
    def incidents_fitting_tristates(
        self,
        data=None,
    ):
        if not data:
            data = self.filter.copy()
        fitting_incidents = self.all_incidents
        filter_open = data.pop("open", None)
        filter_acked = data.pop("acked", None)
        filter_stateful = data.pop("stateful", None)

        if filter_open is True:
            fitting_incidents = fitting_incidents.open()
        if filter_open is False:
            fitting_incidents = fitting_incidents.closed()
        if filter_acked is True:
            fitting_incidents = fitting_incidents.acked()
        if filter_acked is False:
            fitting_incidents = fitting_incidents.not_acked()
        if filter_stateful is True:
            fitting_incidents = fitting_incidents.stateful()
        if filter_stateful is False:
            fitting_incidents = fitting_incidents.stateless()
        return fitting_incidents.distinct()

    # XXX wrong location
    def incidents_fitting_maxlevel(self, data=None):
        if not data:
            data = self.filter.copy()
        maxlevel = data.pop("maxlevel", None)
        if not maxlevel:
            return self.all_incidents.distinct()
        return self.all_incidents.filter(level__lte=maxlevel).distinct()

    # XXX wrong location
    def incident_fits(self, incident: Incident):
        return self.filter_wrapper.incident_fits(incident)

    # XXX wrong location
    def event_fits(self, event: Event):
        return self.filter_wrapper.event_fits(event)


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

    # XXX wrong location
    @property
    def filtered_incidents(self):
        qs = [filter_.filtered_incidents for filter_ in self.filters.all()]
        return reduce(or_, qs)

    # XXX wrong location
    def incident_fits(self, incident: Incident):
        assert incident.source, "incident does not have a source -2"
        if not self.active:
            return False
        is_selected_by_time = self.timeslot.timestamp_is_within_time_recurrences(incident.start_time)
        checks = {f: f.incident_fits(incident) for f in self.filters.all()}
        is_selected_by_filters = False not in checks.values()
        return is_selected_by_time and is_selected_by_filters

    # XXX wrong location
    def event_fits(self, event: Event):
        if not self.active:
            return False
        return any(f.event_fits(event) for f in self.filters.all())
