from django.db import models
from multiselectfield import MultiSelectField

from aas.site.auth.models import User


class NotificationProfile(models.Model):
    user = models.ForeignKey(
        User,
        models.CASCADE,
        related_name='notification_profiles',
    )
    name = models.CharField(max_length=40)
    interval_start = models.DateTimeField()
    interval_stop = models.DateTimeField()

    EMAIL = 'EM'
    SMS = 'SM'
    SLACK = 'SL'
    MEDIA_CHOICES = (
        (EMAIL, "Email"),
        (SMS, "SMS"),
        (SLACK, "Slack"),
    )
    media = MultiSelectField(choices=MEDIA_CHOICES, min_choices=1, default=EMAIL)

    def __str__(self):
        return f"{self.name}: {self.interval_start.time()} - {self.interval_stop.time()}"
