from __future__ import annotations

import functools
from typing import Any, List, Optional, Type, Union, Protocol

from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django import forms


def preferences_manager(namespace):
    class Manager(PreferencesManager):
        def get_queryset(self):
            return super().get_queryset().filter(namespace=namespace)

        def create(self, **kwargs):
            kwargs["namespace"] = namespace
            return super().create(**kwargs)

    return Manager()


def preferences(cls: Optional[type] = None, namespace: Optional[str] = None):
    """Use this decorator to declare a namespaced subclass of ``Preferences`` without manually
    subclassing it. This decorator will add the Preferences model as a base and set the required
    attributes such as the ``_namespace`` and the the ``objects`` Manager instance. If you specify
    a Meta attribute, it will use that class to set the ``proxy`` attribute.

    Use like the following:

    @prefrences(namespace="my_namespace")
    class MyPreferences:
        _FIELD_DEFAULTS = {
          "example_pref": "some value"
        }

    In order to get code/method completion, you can inherit from the ``PreferencesBase`` Protocol,
    but this is optional
    """

    if cls is None:
        return functools.partial(preferences, namespace=namespace)
    if namespace is None:
        raise ValueError("namespace may not be None")

    class Meta:
        pass

    Meta = getattr(cls, "Meta", Meta)
    Meta.proxy = True

    attributes = {
        "_namespace": namespace,
        "objects": preferences_manager(namespace),
        "Meta": Meta,
        "__module__": cls.__module__,
    }

    return type(cls.__name__, (cls, Preferences), attributes)


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

    def get_preferences_context(self):
        pref_sets = Preferences.ensure_for_user(self)
        prefdict = {}
        for pref_set in pref_sets:
            prefdict[pref_set.namespace] = pref_set.get_context()
        return prefdict

    def get_namespaced_preferences(self, namespace):
        obj, _ = Preferences.objects.get_or_create(user=self, namespace=namespace)
        if not obj.preferences and (defaults := obj.get_defaults()):
            obj.preferences = defaults
            obj.save()
        return obj


class PreferencesManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(namespace__in=Preferences.NAMESPACES)

    def get_by_natural_key(self, user, namespace):
        return self.get(user=user, namespace=namespace)

    def get_all_defaults(self):
        prefdict = {}
        for namespace, subclass in Preferences.NAMESPACES.items():
            if defaults := subclass.get_defaults():
                prefdict[namespace] = defaults
        return prefdict


class UnregisteredPreferencesManager(models.Manager):
    def get_queryset(self):
        """Find preferences that are not backed by a subclass

        It *is* possible to create a preference that has no subclass:

        * Directly in database
        * Preferences().save
        * Preferences.objects.create()

        Find them so that they can be handled, preferrably deleted.
        """
        return super().get_queryset().exclude(namespace__in=Preferences.NAMESPACES)


class SessionPreferences:
    def __init__(self, session, namespace):
        self.session = session
        self._namespace = namespace
        self.namespace = namespace
        self.prefclass = Preferences.NAMESPACES[namespace]
        self.FORMS = self.prefclass.FORMS.copy()
        self._FIELD_DEFAULTS = self.prefclass._FIELD_DEFAULTS.copy()
        self.session.setdefault("preferences", dict())
        self.session["preferences"].setdefault(namespace, self.get_defaults())
        self.preferences = self.session["preferences"][namespace]

    def __str__(self):
        return f"anonymous' {self._namespace}"

    def natural_key(self):
        raise NotImplementedError

    @classmethod
    def ensure_for_user(cls, _):
        pass

    def get_instance(self):
        raise NotImplementedError

    def get_defaults(self):
        return self.prefclass.get_defaults()

    def update_context(self, context):
        return self.prefclass.update_context(context)

    def get_context(self):
        return self.prefclass.get_context()

    def get_preference(self, name):
        return self.prefclass.get_preference(name)

    def save_preference(self, name, value):
        self.preferences[name] = value
        self.session["preferences"][self._namespace][name] = value


class PreferencesBase(Protocol):
    FORMS: dict[str, forms.Form]
    _FIELD_DEFAULTS: dict[str, Any]

    @classmethod
    def get_defaults(cls) -> dict[str, Any]:
        pass

    def update_context(self, context: dict[str, Any]) -> dict[str, Any]:
        pass


class Preferences(models.Model):
    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "Users' Preferences"
        constraints = [
            models.UniqueConstraint(name="unique_preference", fields=["user", "namespace"]),
        ]

    NAMESPACES: dict[str, Type[Preferences]] = {}

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="preferences")
    namespace = models.CharField(blank=False, max_length=255)
    preferences = models.JSONField(blank=True, default=dict)

    objects = PreferencesManager()
    unregistered = UnregisteredPreferencesManager()

    # must be set by the subclasses
    FORMS: dict[str, forms.Form]
    _FIELD_DEFAULTS: dict[str, Any]

    # django methods

    # called when subclass is constructing itself
    def __init_subclass__(cls, **kwargs):
        assert isinstance(getattr(cls, "FORMS", None), dict), f"{cls.__name__}.FORMS must be a dictionary"
        assert isinstance(
            getattr(cls, "_FIELD_DEFAULTS", None), dict
        ), f"{cls.__name__}._FIELD_DEFAULTS must be a dictionary"

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
    def get_defaults(cls):
        "Override to add magic"
        return cls._FIELD_DEFAULTS.copy() if cls._FIELD_DEFAULTS else {}

    @classmethod
    def ensure_for_user(cls, user) -> List[Preferences]:
        all_preferences = {p.namespace: p for p in user.preferences.all()}
        valid_preferences = []

        for namespace, subclass in cls.NAMESPACES.items():
            if namespace in all_preferences:
                valid_preferences.append(all_preferences[namespace])
                continue
            obj = subclass.objects.create(user=user, namespace=namespace)
            obj.preferences = subclass.get_defaults()
            obj.save()
            valid_preferences.append(obj)

        return valid_preferences

    def update_context(self, context):
        "Override this to change what is put in context"
        return {}

    def get_context(self):
        """Preferences are put into context via a context_processor

        Note that we *copy* the preferences here. If overriding this method,
        ensure to run super() to get a clean copy.
        """
        context = self.get_defaults() or {}
        context.update(self.preferences.copy())
        context.update(self.update_context(context))
        return context

    def get_preference(self, name):
        return self.preferences.get(name, self.get_defaults().get(name, None))

    def save_preference(self, name, value):
        self.preferences[name] = value
        self.save()
