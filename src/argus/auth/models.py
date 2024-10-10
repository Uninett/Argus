import json

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
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


class PreferencesManager(models.Manager):
    def get_by_natural_key(self, user, namespace):
        return self.get(user=user, namespace=namespace)


class Preferences(models.Model):
    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "Users' Preferences"
        constraints = [
            models.UniqueConstraint(name="unique_preference", fields=["user", "namespace"]),
        ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    namespace = models.CharField(max_length=255, unique=True)
    preferences = models.JSONField(blank=True, default=dict)

    objects = PreferencesManager()

    # django methods

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namespace = self.generate_namespace()

    def __str__(self):
        return "{}'s preferences for {}".format(self.natural_key())

    def save(self, *args, **kwargs):
        if not self.validate_namespace(self.namespace):
            self.namespace = self.generate_namespace()
        super().save(*args, **kwargs)

    def natural_key(self):
        return (self.user, self.namespace)

    # our methods

    @classmethod
    def ensure_for_user(cls, user):
        for cls in cls.__subclasses__():
            cls.objects.get_or_create(user=user)

    @classmethod
    def generate_namespace(cls):
        app_label = cls._meta.app_label
        class_name = cls._meta.object_name
        return f"{app_label}.{class_name}"

    @classmethod
    def validate_namespace(cls, value):
        if namespace := cls.generate_namespace() != value:
            raise ValidationError(f'"namespace" must be "{namespace}"')
