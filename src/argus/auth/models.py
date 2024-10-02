from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    @property
    def is_source_system(self):
        return hasattr(self, "source_system")

    @property
    def is_end_user(self):
        return not hasattr(self, "source_system")

    def create_preferences(self):
        self.save()  # triggers post_save signal


class Preferences(models.Model):
    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "Users' Preferences"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferences = models.JSONField(blank=True, default=dict)

    @classmethod
    def ensure_for_user(cls, user):
        cls.objects.get_or_create(user=user)
