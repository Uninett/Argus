from django.db import models


class LastSeenVersion(models.Model):
    id = models.AutoField(primary_key=True)
    version = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
