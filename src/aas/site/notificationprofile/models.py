from django.db import models
from multiselectfield import MultiSelectField

from aas.site.auth.models import User


class TimeSlotGroup(models.Model):
    class Meta:
        ordering = ['name']

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='time_slot_groups',
    )
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name


class TimeSlot(models.Model):
    MONDAY = 'MO'
    TUESDAY = 'TU'
    WEDNESDAY = 'WE'
    THURSDAY = 'TH'
    FRIDAY = 'FR'
    SATURDAY = 'SA'
    SUNDAY = 'SU'
    DAY_CHOICES = (
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    )
    group = models.ForeignKey(
        to=TimeSlotGroup,
        on_delete=models.CASCADE,
        related_name='time_slots',
    )

    day = models.CharField(max_length=2, choices=DAY_CHOICES)
    start = models.DateTimeField()  # TimeField?
    end = models.DateTimeField()



class NotificationProfile(models.Model):
    user = models.ForeignKey(
        User,
        models.CASCADE,
        related_name='notification_profiles',
    )
    group = models.ForeignKey(
        to=TimeSlotGroup,
        on_delete=models.CASCADE,
        related_name='notification_profiles',
    )

    EMAIL = 'EM'
    SMS = 'SM'
    SLACK = 'SL'
    MEDIA_CHOICES = (
        (EMAIL, "Email"),
        (SMS, "SMS"),
        (SLACK, "Slack"),
    )
    media = MultiSelectField(choices=MEDIA_CHOICES, min_choices=1, default=EMAIL)

    # TODO: name based on filter and time_slot_group
    # def __str__(self):
    #     return
