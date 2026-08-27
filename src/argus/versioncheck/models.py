from django.db import models
from django.utils.timezone import now


class PyPIVersion(models.Model):
    id = models.AutoField(primary_key=True)
    version = models.CharField(max_length=20, unique=True)
    upload_time = models.DateTimeField(default=now)
    timestamp = models.DateTimeField(default=now)

    class Meta:
        ordering = ["-upload_time"]

    def __str__(self):
        return f"v{self.version}/{self.upload_time}"
