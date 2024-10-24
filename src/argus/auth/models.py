from typing import Union

from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    @property
    def is_source_system(self):
        return hasattr(self, "source_system")

    @property
    def is_end_user(self):
        return not hasattr(self, "source_system")

    def is_member_of_group(self, group: Union[str, Group]):
        if isinstance(group, str):
            try:
                group = Group.objects.get(name=group)
            except Group.DoesNotExist:
                return None
        return group in self.groups.all()


class PreferencesManager(models.Manager):
    def get_by_natural_key(self, user, namespace):
        return self.get(user=user, namespace=namespace)

    def create_missing_preferences(self):
        precount = Preferences.objects.count()
        for namespace, subclass in Preferences.NAMESPACES.items():
            for user in User.objects.all():
                Preferences.ensure_for_user(user)
        return (precount, Preferences.objects.count())


class SubclassMixin:
    @classmethod
    def generate_namespace(cls):
        app_label = cls.app_label
        class_name = cls.class_name
        return f"{app_label}.{class_name}"


class Preferences(models.Model):
    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "Users' Preferences"
        constraints = [
            models.UniqueConstraint(name="unique_preference", fields=["user", "namespace"]),
        ]

    NAMESPACES = {}

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="preferences")
    namespace = models.CharField(blank=False, max_length=255)
    preferences = models.JSONField(blank=True, default=dict)

    objects = PreferencesManager()

    # django methods

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        namespace = cls.generate_namespace()
        cls.NAMESPACES[namespace] = cls

    def __str__(self):
        return f"{self.user}'s {self.namespace}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_instance()

    def natural_key(self):
        return (self.user, self.namespace)

    # our methods

    @classmethod
    def get_namespace_mapping(cls):
        mapping = {}
        for namespace, subclass in cls.NAMESPACES.items():
            mapping[subclass] = namespace
        return mapping

    def get_instance(self):
        subclass = self.NAMESPACES.get(self.namespace, None)
        if subclass:
            self.__class__ = subclass

    @classmethod
    def ensure_for_user(cls, user):
        for namespace, subclass in cls.NAMESPACES.items():
            subclass.objects.get_or_create(user=user, namespace=namespace)

    @classmethod
    def validate_namespace(cls, value):
        if (namespace := cls.generate_namespace()) != value:
            raise ValidationError(f'"namespace" must be "{namespace}"')
