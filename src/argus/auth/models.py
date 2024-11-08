from typing import Union

from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.db import models


def preferences_manager_factory(namespace):
    class Manager(PreferencesManager):
        def get_queryset(self):
            return super().get_queryset().filter(namespace=namespace)

        def create(self, **kwargs):
            kwargs["namespace"] = namespace
            return super().create(**kwargs)

    return Manager


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

    def is_used(self):
        # user has created events
        if self.caused_events.exists():
            return True

        # user is a source system that has created incidents
        source = getattr(self, "source_system", None)
        if source and source.incidents.exists():
            return True

        # notification_profiles: manually created but user is safe to
        # delete
        # timeslots: autocreated per person user
        # destinations: autocreated per user with email via social auth

        # user is not considered in use
        return False

    def get_or_create_preferences(self):
        Preferences.ensure_for_user(self)
        return self.preferences.all()

    def get_preferences_context(self):
        pref_sets = self.get_or_create_preferences()
        prefdict = {}
        for pref_set in pref_sets:
            prefdict[pref_set._namespace] = pref_set.get_context()
        return prefdict

    def get_namespaced_preferences(self, namespace):
        return self.get_or_create_preferences().get(namespace=namespace)


class PreferencesManager(models.Manager):
    def get_by_natural_key(self, user, namespace):
        return self.get(user=user, namespace=namespace)

    def create_missing_preferences(self):
        precount = Preferences.objects.count()
        for namespace, subclass in Preferences.NAMESPACES.items():
            for user in User.objects.all():
                Preferences.ensure_for_user(user)
        return (precount, Preferences.objects.count())

    def get_all_defaults(self):
        prefdict = {}
        for namespace, subclass in Preferences.NAMESPACES.items():
            if subclass.FIELD_DEFAULTS:
                prefdict[namespace] = subclass.FIELD_DEFAULTS
        return prefdict


class SessionPreferences:
    def __init__(self, session, namespace):
        self.session = session
        self._namespace = namespace
        self.namespace = namespace
        self.prefclass = Preferences.NAMESPACES[namespace]
        self.FORMS = self.prefclass.FORMS.copy()
        self.FIELD_DEFAULTS = self.prefclass.FIELD_DEFAULTS.copy()
        self.session.setdefault("preferences", dict())
        self.session["preferences"].setdefault(namespace, self.FIELD_DEFAULTS)
        self.preferences = self.session["preferences"][namespace]

    def __str__(self):
        return f"anonymous' {self._namespace}"

    def natural_key(self):
        raise NotImplementedError

    @classmethod
    def ensure_for_user(cls, _):
        pass

    def update_context(self, context):
        return self.prefclass.update_context(context)

    def get_context(self):
        return self.prefclass.get_context()

    def get_preference(self, name):
        return self.prefclass.get_preference(name)

    def save_preference(self, name, value):
        self.preferences[name] = value
        self.session["preferences"][self._namespace][name] = value


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

    # storage for field forms in preference
    FORMS = None
    # storage for field defaults in preference
    FIELD_DEFAULTS = None

    # django methods

    # called when subclass is constructing itself
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.NAMESPACES[cls._namespace] = cls

    def __str__(self):
        return f"{self.user}'s {self.namespace}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_instance()

    def natural_key(self):
        return (self.user, self.namespace)

    # our methods

    def get_instance(self):
        subclass = self.NAMESPACES.get(self.namespace, None)
        if subclass:
            self.__class__ = subclass

    @classmethod
    def ensure_for_user(cls, user):
        for namespace, subclass in cls.NAMESPACES.items():
            obj, _ = subclass.objects.get_or_create(user=user, namespace=namespace)
            if not obj.preferences and subclass.FIELD_DEFAULTS:
                obj.preferences = subclass.FIELD_DEFAULTS
                obj.save()

    def update_context(self, context):
        "Override this to change what is put in context"
        return {}

    def get_context(self):
        """Preferences are put into context via a context_processor

        Note that we *copy* the preferences here. If overriding this method,
        ensure to run super() to get a clean copy.
        """
        context = self.FIELD_DEFAULTS.copy() if self.FIELD_DEFAULTS else {}
        context.update(self.preferences.copy())
        context.update(self.update_context(context))
        return context

    def get_preference(self, name):
        return self.preferences.get(name, self.FIELD_DEFAULTS.get(name, None))

    def save_preference(self, name, value):
        self.preferences[name] = value
        self.save()
