from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from ..models import DestinationConfig

if TYPE_CHECKING:
    from collections.abc import Iterable

    from types import NoneType
    from typing import Union, Generator

    from django.contrib.auth import get_user_model
    from django.db.models.query import QuerySet

    from argus.incident.models import Event

    User = get_user_model()


__all__ = ["NotificationMedium"]


class CommonDestinationConfigForm(forms.ModelForm):
    class Meta:
        model = DestinationConfig
        fields = ["label", "media"]

    def __init__(self, user, **kwargs):
        self.user = user
        super().__init__(**kwargs)


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

    error_messages = {
        "readonly_medium": "Media cannot be updated, only settings.",
        "readonly_user": "User cannot be changed, only settings.",
        "settings_type": "Settings has to be a dictionary.",
        "empty_settings": '"settings" cannot be empty',
    }

    class NotDeletableError(Exception):
        """
        Custom exception class that is raised when a destination cannot be
        deleted
        """

    @classmethod
    def validate(cls, data: dict, user: User, instance: DestinationConfig = None) -> CommonDestinationConfigForm:
        if instance:
            if data.get("media", "") != instance.media.slug:
                code = "readonly_media"
                message = cls.error_messages["readonly_media"]
                raise DRFValidationError(detail={"media": message}, code=code)
            if instance.user != user:
                code = "readonly_user"
                message = cls.error_messages["readonly_user"]
                raise DRFValidationError(detail={"user": message}, code=code)
            form = CommonDestinationConfigForm(data, instance=instance)
        else:
            form = CommonDestinationConfigForm(data)

        if not form.is_valid():
            code = "invalid"
            detail = form.errors.get_json_data()
            raise DRFValidationError(detail=detail, code=code)

        settings = data["settings"]
        if not isinstance(settings, dict):
            code = "settings_type"
            message = cls.error_messages["settings_type"]
            raise DRFValidationError(detail={"settings": message}, code=code)
        if not settings:
            code = "empty_settings"
            message = cls.error_messages["empty_settings"]
            raise DRFValidationError(detail={"settings": message}, code=code)
        settings_form = cls.validate_settings(data["settings"], user, instance=instance)
        if not settings_form.is_valid():
            code = "invalid"
            detail = settings_form.errors.get_json_data()
            raise DRFValidationError(detail=detail, code=code)
        form.cleaned_data["settings"] = settings_form.cleaned_data
        form.cleaned_data["user"] = user
        return form

    @classmethod
    def validate_settings(
        cls,
        data: dict,
        user: User,
        instance: DestinationConfig = None,
        prefix: str = "",
    ) -> forms.Form:
        """
        Validates the settings of destination and returns a dict with
        validated and cleaned data
        """
        initial = {}
        if instance:
            initial = instance.settings
        form = cls.Form(data=data, initial=initial, prefix=prefix)
        if not form.is_valid():
            return form

        form = cls.clean(form, instance)

        if cls.has_duplicate(user.destinations, form.cleaned_data):
            form.add_error(
                None,
                DjangoValidationError(
                    "A %(media)s destination with this %(key) already exists",
                    code="duplicate",
                    params={
                        "media": cls.MEDIA_SLUG,
                        "key": cls.MEDIA_SETTINGS_KEY,
                    },
                ),
            )
        return form

    @classmethod
    def clean(cls, form: forms.Form, instance: DestinationConfig = None) -> forms.Form:
        """Can change the cleaned data and errors list of a valid form"""
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
        Returns a descriptive label for this destination if none is stored
        """
        return destination.label if destination.label else destination.settings.get(cls.MEDIA_SETTINGS_KEY)

    # No querysets beyond this point!

    @classmethod
    def _get_relevant_destinations(cls, destinations: Iterable[DestinationConfig]) -> Generator[DestinationConfig]:
        return (destination for destination in destinations if destination.media_id == cls.MEDIA_SLUG)

    @classmethod
    def get_relevant_destination_settings(cls, destinations: Iterable[DestinationConfig]) -> set[str]:
        """Returns a set of addresses the message should be sent to"""
        destinations = [
            destination.settings[cls.MEDIA_SETTINGS_KEY] for destination in cls._get_relevant_destinations(destinations)
        ]
        return set(destinations)

    get_relevant_addresses = get_relevant_destination_settings

    @classmethod
    @abstractmethod
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], **kwargs) -> bool:
        """Sends message about a given event to the given destinations"""
        pass

    @classmethod
    def is_not_deletable(cls, destination: DestinationConfig) -> dict[str, Any]:
        """
        Flag if the destination cannot be deleted

        Returns an empty dict (falsey) if the destination is deletable.
        Returns a dict (truthy) if the destination is not deletable.

        Structure of dict::

            {label: error_message}
        """
        connected_profiles = destination.notification_profiles.all()
        if connected_profiles:
            profiles = ", ".join([str(profile) for profile in connected_profiles])
            error_msg = f"Destination in use by profile(s): {profiles}."
            return {"profiles": error_msg}
        return {}

    @classmethod
    def raise_if_not_deletable(cls, destination: DestinationConfig) -> NoneType:
        """
        Raises a NotDeletableError if the given destination is not able to be deleted
        (if it is in use by any notification profiles)
        """
        errors = cls.is_not_deletable(destination)
        if errors:
            message = " ".join(errors.values())
            raise cls.NotDeletableError(f"Cannot delete this destination: {message}.")

    @classmethod
    def _update_destination(cls, destination: DestinationConfig, validated_data: dict) -> DestinationConfig:
        # adapted from rest_framework.serializers.ModelSerializer.update
        # DestinationConfig MUST NOT have any m2m-relations so this is safe

        for attr, value in validated_data.items():
            setattr(destination, attr, value)

        return destination

    @classmethod
    def update(cls, destination: DestinationConfig, validated_data: dict) -> Union[DestinationConfig, NoneType]:
        """
        Updates a destination

        Override in case the normal update function is not sufficient
        """
        instance = cls._update_destination(destination, validated_data)
        instance.save()
        return instance
