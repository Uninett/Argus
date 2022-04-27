from __future__ import annotations

import json
from datetime import datetime, time
from functools import reduce
from operator import or_
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from multiselectfield import MultiSelectField

from argus.auth.models import User

from .constants import DEPRECATED_FILTER_NAMES

if TYPE_CHECKING:
    from argus.incident.models import Incident


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


class FilterWrapper:
    TRINARY_FILTERS = ("open", "acked", "stateful")

    def __init__(self, filterblob):
        self.fallback_filter = getattr(settings, "ARGUS_FALLBACK_FILTER", {})
        self.filter = filterblob

    def _get_tristate(self, tristate):
        fallback_filter = self.fallback_filter.get(tristate, None)
        return self.filter.get(tristate, fallback_filter)

    def are_tristates_empty(self):
        for tristate in self.TRINARY_FILTERS:
            if self._get_tristate(tristate) is not None:
                return False
        return True

    def is_maxlevel_empty(self):
        fallback_filter = self.fallback_filter.get("maxlevel", None)
        return not self.filter.get("maxlevel", fallback_filter)

    @property
    def is_empty(self):
        return self.are_tristates_empty() and self.is_maxlevel_empty()

    def _incident_is_tristate(self, tristate, incident):
        return getattr(incident, tristate, None)

    def incident_fits_tristates(self, incident):
        if self.are_tristates_empty():
            return None
        fits_tristates = []
        for tristate in self.TRINARY_FILTERS:
            filter_tristate = self._get_tristate(tristate)
            if filter_tristate is None:
                continue
            incident_tristate = self._incident_is_tristate(tristate, incident)
            fits_tristates.append(filter_tristate == incident_tristate)
        return all(fits_tristates)

    def incident_fits_maxlevel(self, incident):
        if self.is_maxlevel_empty():
            return None
        fallback_filter = self.fallback_filter.get("maxlevel", None)
        return incident.level <= min(filter(None, (self.filter["maxlevel"], fallback_filter)))

    def incident_fits(self, incident):
        return self.incident_fits_tristates(incident) and self.incident_fits_maxlevel(incident)


class Filter(models.Model):
    FILTER_NAMES = set(DEPRECATED_FILTER_NAMES)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="filters")
    name = models.CharField(max_length=40)
    filter_string = models.TextField()
    filter = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "user"], name="%(class)s_unique_name_per_user")]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_wrapper = FilterWrapper(self.filter)

    def __str__(self):
        return f"{self.name} [{self.filter_string}]"

    @property
    def filter_json(self):
        return json.loads(self.filter_string)

    def _old_is_empty(self):
        data = self.filter_json
        for value in data.values():
            if value:
                return False
        return True

    @property
    def is_empty(self):
        old = self._old_is_empty()
        new = self.filter_wrapper.is_empty
        return all((old, new))

    @property
    def all_incidents(self):
        # Prevent cyclical import
        from argus.incident.models import Incident

        return Incident.objects.all()

    @property
    def filtered_incidents(self):
        if self.is_empty:
            return self.all_incidents.none().distinct()
        data = self.filter_json
        filtered_by_source = self.incidents_with_source_systems(data)
        filtered_by_tags = self.incidents_with_tags(data)
        return filtered_by_source & filtered_by_tags

    def incidents_with_source_systems(self, data=None):
        if not data:
            data = self.filter_json
        source_list = data.pop("sourceSystemIds", [])
        if source_list:
            return self.all_incidents.filter(source__in=source_list).distinct()
        return self.all_incidents.distinct()

    def source_system_fits(self, incident: Incident, data=None):
        if not data:
            data = self.filter_json
        source_list = data.pop("sourceSystemIds", [])
        if not source_list:
            # We're not limiting on sources!
            return None
        return incident.source.id in source_list

    def incidents_with_tags(self, data=None):
        if not data:
            data = self.filter_json
        tags_list = data.pop("tags", [])
        if tags_list:
            return self.all_incidents.from_tags(*tags_list)
        return self.all_incidents.distinct()

    def tags_fit(self, incident: Incident, data=None):
        if not data:
            data = self.filter_json
        tags_list = data.pop("tags", [])
        if not tags_list:
            # We're not limiting on tags!
            return None
        tags = set(tag.representation for tag in incident.deprecated_tags)
        return tags.issuperset(tags_list)

    def incident_fits(self, incident: Incident):
        if self.is_empty:
            return False  # Filter is empty!
        data = self.filter_json
        source_fits = self.source_system_fits(incident, data)
        tags_fit = self.tags_fit(incident, data)
        new_filters_fit = self.filter_wrapper.incident_fits(incident)
        # If False then one filter failed
        checks = set((source_fits, tags_fit, new_filters_fit))
        return not (False in checks)  # At least one filter failed


class Media(models.Model):
    class Meta:
        verbose_name = "Medium"
        verbose_name_plural = "Media"

    MEDIA_NAME_LENGTH = 20
    slug = models.SlugField(max_length=MEDIA_NAME_LENGTH, blank=True, primary_key=True)
    name = models.CharField(max_length=MEDIA_NAME_LENGTH)

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

    @property
    def filtered_incidents(self):
        qs = [filter_.filtered_incidents for filter_ in self.filters.all()]
        return reduce(or_, qs)

    def incident_fits(self, incident: Incident):
        assert incident.source, "incident does not have a source -2"
        if not self.active:
            return False
        is_selected_by_time = self.timeslot.timestamp_is_within_time_recurrences(incident.start_time)
        is_selected_by_filters = any(f.incident_fits(incident) for f in self.filters.all())
        return is_selected_by_time and is_selected_by_filters
