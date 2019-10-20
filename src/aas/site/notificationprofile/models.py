from django.db import models

from ..auth.models import User


class NotificationProfile(models.Model):
    user = models.ForeignKey(
        User,
        models.CASCADE,
    )
    name = models.CharField(max_length=40)
    interval_start = models.DateTimeField()
    interval_stop = models.DateTimeField()
