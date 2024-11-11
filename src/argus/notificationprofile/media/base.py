from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from rest_framework.exceptions import ValidationError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from types import NoneType
    from typing import Union

    from django.contrib.auth import get_user_model
    from django.db.models.query import QuerySet

    from argus.incident.models import Event
    from ..models import DestinationConfig
    from ..serializers import RequestDestinationConfigSerializer

    User = get_user_model()


__all__ = ["NotificationMedium"]


class NotificationMedium(ABC):
    """
    Must be defined by subclasses:

    Class attributes:

    - MEDIA_SLUG: short string id for the medium, lowercase
    - MEDIA_NAME: human friendly id for the medium
    - MEDIA_SETTINGS_KEY: the field in settings that is specific for this medium
    - MEDIA_JSON_SCHEMA: A json-schema to describe the settings field to
      javascript, used by the API
    - Form: a django.forms.Form that validates the contents of the
      settings-field. MEDIA_SETTINGS_KEY must be the field-name of a required
      field in the form.

    Class methods:

    - send(event, destinations): How to send the given event to the given
      destinations of type MEDIA_SLUG.
    """

    class NotDeletableError(Exception):
        """
        Custom exception class that is raised when a destination cannot be
        deleted
        """

    @classmethod
    def validate(cls, instance: RequestDestinationConfigSerializer, dict_: dict, user: User) -> dict:
        """
        Validates the settings of destination and returns a dict with
        validated and cleaned data
        """
        form = cls.Form(dict_["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)
        return form.cleaned_data

        form = cls.clean(form)

        if cls.has_duplicate(user.destinations):
            raise ValidationError(cls.MEDIA_SETTINGS_KEY, f"{cls.MEDIA_NAME} already exists")

        return form.cleaned_data

    @classmethod
    def clean(cls, form):
        """Can change the cleaned data of a valid form"""
        return form

    @classmethod
    def has_duplicate(cls, queryset: QuerySet, settings: dict) -> bool:
        """
        Returns True if a destination with the given settings already exists
        in the given queryset
        """
        key = f"settings__{cls.MEDIA_SETTINGS_KEY}"
        value = settings[cls.MEDIA_SETTINGS_KEY]
        return queryset.filter(media_id=cls.MEDIA_SLUG, **{key: value}).exists()

    @classmethod
    def get_label(cls, destination: DestinationConfig) -> str:
        """
        Returns a descriptive label for this destination.
        """
        return destination.settings.get(cls.MEDIA_SETTINGS_KEY)

    # No querysets beyond this point!

    @classmethod
    def get_relevant_destinations(cls, destinations: Iterable[DestinationConfig]) -> Set[DestinationConfig]:
        """Returns a set of addresses the message should be sent to"""
        destinations = [
            destination.settings[cls.MEDIA_SETTINGS_KEY]
            for destination in destinations
            if destination.media_id == cls.MEDIA_SLUG
        ]
        return set(destinations)

    get_relevant_addresses = get_relevant_destinations

    @classmethod
    @abstractmethod
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], **kwargs) -> bool:
        """Sends message about a given event to the given destinations"""
        pass

    @classmethod
    def raise_if_not_deletable(cls, destination: DestinationConfig) -> NoneType:
        """
        Raises a NotDeletableError if the given destination is not able to be deleted
        (if it is in use by any notification profiles)
        """
        connected_profiles = destination.notification_profiles.all()
        if connected_profiles:
            profiles = ", ".join([str(profile) for profile in connected_profiles])
            raise cls.NotDeletableError(
                f"Cannot delete this destination since it is in use in the notification profile(s): {profiles}."
            )

    @staticmethod
    def update(destination: DestinationConfig, validated_data: dict) -> Union[DestinationConfig, NoneType]:
        """
        Updates a destination in case the normal update function is not
        sufficient and returns the updated destination in that case,
        returns None otherwise
        """
        return None
