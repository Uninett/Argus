from django.db import models

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

    def __str__(self):
        return f"{self.name}: {self.interval_start.time()} - {self.interval_stop.time()}"
