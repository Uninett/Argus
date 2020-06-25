import json
from datetime import datetime, time

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from multiselectfield import MultiSelectField

from aas.alert.models import Alert
from aas.auth.models import User
from .utils import AttrGetter, NestedAttrGetter


class TimeSlot(models.Model):
    user = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="time_slots",
    )
    name = models.CharField(max_length=40)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "user"], name="timeslot_unique_name_per_user",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name

    def timestamp_is_within_time_intervals(self, timestamp: datetime):
        for time_interval in self.time_intervals.all():
            if time_interval.timestamp_is_within(timestamp):
                return True
        return False

    # Create default immediate TimeSlot when a user is created
    @staticmethod
    @receiver(post_save, sender=User)
    def create_default_time_slot(sender, instance, created, raw, *args, **kwargs):
        if raw or not created:
            return

        time_slot = TimeSlot.objects.create(user=instance, name="Immediately")
        time_interval_start, time_interval_end = (
            TimeInterval.DAY_START,
            TimeInterval.DAY_END,
        )
        for day, _day_name in TimeInterval.DAY_CHOICES:
            TimeInterval.objects.create(
                time_slot=time_slot,
                day=day,
                start=time_interval_start,
                end=time_interval_end,
            )


class TimeInterval(models.Model):
    DAY_START = time.min
    DAY_END = time.max

    MONDAY = "MO"
    TUESDAY = "TU"
    WEDNESDAY = "WE"
    THURSDAY = "TH"
    FRIDAY = "FR"
    SATURDAY = "SA"
    SUNDAY = "SU"
    DAY_CHOICES = (
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    )
    # Map day name to ISO index, e.g. "MO": 1
    DAY_NAME_TO_INDEX = {day: i + 1 for i, (day, _) in enumerate(DAY_CHOICES)}

    time_slot = models.ForeignKey(
        to=TimeSlot, on_delete=models.CASCADE, related_name="time_intervals",
    )

    day = models.CharField(max_length=2, choices=DAY_CHOICES)
    start = models.TimeField(help_text="Local time.")
    end = models.TimeField(help_text="Local time.")

    # TODO: is this method needed?
    """
    def __eq__(self, other):
        if type(other) is not TimeInterval:
            return False
        if super().__eq__(other):
            return True
        return (
                self.day == other.day
                and self.start == other.start
                and self.end == other.end
        )
    """

    def __str__(self):
        return f"{self.start}-{self.end} on {self.get_day_display()}s"

    @property
    def isoweekday(self):
        return self.DAY_NAME_TO_INDEX[self.day]

    def timestamp_is_within(self, timestamp: datetime):
        # FIXME: Might affect performance negatively if calling this method frequently
        timestamp = timestamp.astimezone(timezone.get_current_timezone())
        return (
            timestamp.isoweekday() == self.isoweekday
            and self.start <= timestamp.time() <= self.end
        )


class Filter(models.Model):
    FILTER_STRING_FIELDS = {
        "sourceIds": AttrGetter("source"),
        "objectTypeIds": NestedAttrGetter("object.type"),
        "parentObjectIds": AttrGetter("parent_object"),
        "problemTypeIds": AttrGetter("problem_type"),
    }

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="filters",)
    name = models.CharField(max_length=40)
    filter_string = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "user"], name="filter_unique_name_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.name} [{self.filter_string}]"

    @property
    def filter_json(self):
        return json.loads(self.filter_string)

    @property
    def filtered_alerts(self):
        return Alert.objects.filter(self.get_alert_query()).prefetch_default_related()

    def get_alert_query(self):
        json_dict = self.filter_json
        alert_query = Q()
        for filter_field_name, attr_getter in self.FILTER_STRING_FIELDS.items():
            filter_field_value_list = json_dict[filter_field_name]
            if filter_field_value_list:
                alert_arg = {f"{attr_getter.query}__in": filter_field_value_list}
                alert_query &= Q(**alert_arg)
        return alert_query

    def alert_fits(self, alert: Alert):
        json_dict = self.filter_json
        for filter_field_name, attr_getter in self.FILTER_STRING_FIELDS.items():
            filter_field_value_set = set(json_dict[filter_field_name])
            if filter_field_value_set:
                alert_attr = attr_getter(alert)
                if alert_attr.pk not in filter_field_value_set:
                    return False
        return True


class NotificationProfile(models.Model):
    user = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="notification_profiles",
    )
    # TODO: add constraint that user must be the same
    time_slot = models.OneToOneField(
        to=TimeSlot,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="notification_profile",
    )
    filters = models.ManyToManyField(to=Filter, related_name="notification_profiles",)

    EMAIL = "EM"
    SMS = "SM"
    SLACK = "SL"
    MEDIA_CHOICES = (
        (EMAIL, "Email"),
        (SMS, "SMS"),
        (SLACK, "Slack"),
    )
    # TODO: support for multiple email addresses / phone numbers / Slack users
    media = MultiSelectField(choices=MEDIA_CHOICES, min_choices=1, default=EMAIL)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.time_slot}: {', '.join(str(f) for f in self.filters.all())}"

    @property
    def filtered_alerts(self):
        alert_query = Q()
        for filter_ in self.filters.all():
            alert_query |= filter_.get_alert_query()

        return Alert.objects.filter(alert_query).prefetch_default_related()

    def alert_fits(self, alert: Alert):
        if not self.active:
            return False
        return self.time_slot.timestamp_is_within_time_intervals(
            alert.timestamp
        ) and any(f.alert_fits(alert) for f in self.filters.all())
