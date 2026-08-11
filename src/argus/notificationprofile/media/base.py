from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any

try:
    from apprise import Apprise
except ImportError:
    Apprise = None

from django import forms
from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string

from argus.notificationprofile.models import DestinationConfig
from argus.constants import API_STABLE_VERSION
from argus.notificationprofile.models import Media
from argus.notificationprofile.utils import are_notifications_enabled
from argus.util.datetime_utils import INFINITY, LOCAL_INFINITY

if TYPE_CHECKING:
    from collections.abc import Iterable

    from types import NoneType
    from typing import Optional

    from django.contrib.auth import get_user_model
    from django.db.models.query import QuerySet

    from argus.incident.models import Event

    User = get_user_model()


__all__ = ["NotificationMedium", "AppriseMedium"]

LOG = logging.getLogger(__name__)


def modelinstance_to_dict(obj):
    dict_ = vars(obj).copy()
    dict_.pop("_state")
    return dict_


class CommonDestinationConfigForm(forms.ModelForm):
    class Meta:
        model = DestinationConfig
        fields = ["label", "media", "settings"]

    # Settings is being set as not required for the field required errors from the plugin forms to bubble up
    def __init__(self, *args, **kwargs):
        super(CommonDestinationConfigForm, self).__init__(*args, **kwargs)
        self.fields["settings"].required = False


class NotificationMedium(ABC):
    """
    Must be defined by subclasses:

    Class attributes:

    - MEDIA_SLUG: short string id for the medium, lowercase
    - MEDIA_NAME: human friendly id for the medium
    - MEDIA_SETTINGS_KEY: the field in settings that is specific for this medium
    - MEDIA_JSON_SCHEMA: A json-schema to describe the settings field to
      javascript, used by the API

    Class methods:

    - send(event, destinations): How to send the given event to the given
      destinations of type MEDIA_SLUG.
    """

    class NotDeletableError(Exception):
        """
        Custom exception class that is raised when a destination cannot be
        deleted
        """

    def __init__(self, version: str = API_STABLE_VERSION):
        self.version = version

    @classmethod
    def validate(
        cls, data: dict, user: User, instance: Optional[DestinationConfig] = None
    ) -> CommonDestinationConfigForm:
        """
        Validates that a destination can be created/updated with the given values

        Returns a form with the cleaned data if all is valid and raises a
        ValidationError if not
        """
        if instance:
            cls.validate_instance(data, user, instance)

            # Copy attributes of the destination to avoid field required errors
            for field in CommonDestinationConfigForm.Meta.fields:
                if field not in data and getattr(instance, field):
                    data[field] = getattr(instance, field)

        form = CommonDestinationConfigForm(data)

        # Check that the label and medium are valid values
        if not form.is_valid():
            code = "invalid"
            detail = form.errors.get_json_data()
            raise forms.ValidationError(message=detail, code=code)

        # Check that no destination with this medium and label already exists for this user
        qs = user.destinations.filter(media_id=data.get("media"))
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if data.get("label") and qs.filter(label=data.get("label")).exists():
            code = "duplicate_label"
            message = Media.error_messages["duplicate_label"]
            raise forms.ValidationError(message={"label": message}, code=code)

        # Check that the settings are valid
        settings = data.get("settings", {})
        if not isinstance(settings, dict):
            code = "settings_type"
            message = Media.error_messages["settings_type"]
            raise forms.ValidationError(message={"settings": message}, code=code)

        cleaned_settings = cls.validate_settings(settings, user, instance=instance)
        form.cleaned_data["settings"] = cleaned_settings
        form.cleaned_data["user"] = user
        return form

    @classmethod
    def validate_instance(cls, data: dict, user: User, instance: DestinationConfig):
        """
        Validates that none of the readonly fields of an instance are being
        changed

        Raises a ValidationError if they are
        """
        if data.get("media") and data.get("media").slug != instance.media.slug:
            code = "readonly_media"
            message = Media.error_messages["readonly_media"]
            raise forms.ValidationError(message={"media": [message]}, code=code)

        if instance.user != user:
            code = "readonly_user"
            message = Media.error_messages["readonly_user"]
            raise forms.ValidationError(message={"user": [message]}, code=code)

    @classmethod
    def validate_settings(
        cls,
        data: dict,
        user: User,
        instance: Optional[DestinationConfig] = None,
    ) -> dict:
        """
        Validates the settings of a destination and returns a cleaned settings
        dict and raises a ValidationError if the settings are invalid
        """
        form = cls.Form(data=data)

        if not form.is_valid():
            code = "invalid"
            message = form.errors.get_json_data()
            raise forms.ValidationError(message=message, code=code)

        qs = user.destinations
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if cls.has_duplicate(qs, form.cleaned_data):
            code = "duplicate"
            detail = Media.error_messages["duplicate"]
            raise forms.ValidationError(message=detail, code=code)

        return form.cleaned_data

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

    @classmethod
    def get_relevant_address(cls, destination: DestinationConfig) -> Any:
        """
        Returns the "address" to send the message to
        """
        return destination.settings[cls.MEDIA_SETTINGS_KEY]

    @classmethod
    def get_relevant_destinations(cls, destinations: Iterable[DestinationConfig]) -> set[DestinationConfig]:
        "Return only destinations of the correct type"
        return set(dest for dest in destinations if dest.media_id == cls.MEDIA_SLUG)

    # XXX: deprecated! Use decorator when on Python 3.13
    @classmethod
    def get_relevant_addresses(cls, destinations: Iterable[DestinationConfig]) -> set[Any]:
        """
        Returns a set of addresses the message should be sent to

        Deprecated: Use ``cls.get_relevant_destinations`` with
        ``cls.get_relevant_address`` in a loop instead, in order to make it
        possible to log every tried destination.
        """
        addresses = [
            cls.get_relevant_address(destination) for destination in cls.get_relevant_destinations(destinations)
        ]
        return set(addresses)

    @classmethod
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], **kwargs) -> bool:
        """
        Sends message about a given event to the given destinations

        Loops over the destinations from ``cls.get_relevant_destinations`` and
        converts each destination to a medium-specific "address" via
        ``cls.get_relevant_address``.

        Returns a boolean:
        * True: everything ok
        * False: at least one destination failed
        """
        if not are_notifications_enabled():
            LOG.info("notifications: turned off sitewide, not sending")
            return False

    @classmethod
    def raise_if_not_deletable(cls, destination: DestinationConfig) -> NoneType:
        """
        Raises a NotDeletableError if the given destination cannot be deleted

        Potential reasons:

        * it is marked as "managed", which means it is usable but read-only for end-users
        * it is in use by at least one notification profile
        """
        if destination.managed:
            raise cls.NotDeletableError("Cannot delete this destination since it was defined by an outside source.")

        connected_profiles = destination.notification_profiles.all()
        if connected_profiles:
            profiles = ", ".join([str(profile) for profile in connected_profiles])
            raise cls.NotDeletableError(
                f"Cannot delete this destination since it is in use in the notification profile(s): {profiles}."
            )

    @staticmethod
    @transaction.atomic()
    def update(destination: DestinationConfig, validated_data: dict) -> DestinationConfig | NoneType:
        """Updates a destination

        If the destination is marked as managed and the settings are being updated,
        a copy of the original will be made before changing the destination.
        """
        if "label" in validated_data and (
            "settings" not in validated_data or destination.settings == validated_data["settings"]
        ):
            destination.label = validated_data.get("label")
            destination.save()
            return destination

        original_destination = {}
        if destination.managed:
            # copy the managed destination to create a clone after the changes are
            # applied to the original destination
            # this needs to be done this way due to the 'unique_destination_per_user'
            # constraint on destinations
            original_destination = {
                "user": destination.user,
                "media_id": destination.media_id,
                # don't create a label in order to avoid duplicate label
                "settings": destination.settings.copy(),
                "managed": True,
            }

        # update destination with known id instead of returning a new one
        destination.label = validated_data.get("label", destination.label)
        settings = validated_data.get("settings", destination.settings)
        settings.pop("synced", None)
        destination.settings = settings
        destination.managed = False
        destination.save()

        if original_destination:
            # finally clone the original destination
            managed_destination = DestinationConfig(**original_destination)
            managed_destination.save()

        return destination


class AppriseMedium(NotificationMedium):
    MEDIA_SLUG = "apprise"
    MEDIA_NAME = "Apprise"
    MEDIA_SETTINGS_KEY = "destination_url"
    MEDIA_JSON_SCHEMA = {
        "title": "Apprise Settings",
        "description": "Settings for a DestinationConfig using Apprise.",
        "type": "object",
        "required": [MEDIA_SETTINGS_KEY],
        "properties": {
            MEDIA_SETTINGS_KEY: {
                "type": "string",
                "title": "Apprise destination url",
            }
        },
    }

    class Form(forms.Form):
        destination_url = forms.URLField()

    @staticmethod
    def create_message_context(event: Event):
        """Creates the subject and message for the Apprise notification"""
        title = f"{event}"
        incident_dict = modelinstance_to_dict(event.incident)
        for field in ("id", "source_id"):
            incident_dict.pop(field)
        incident_dict["details_url"] = event.incident.pp_details_url()
        if event.incident.end_time in {INFINITY, LOCAL_INFINITY}:
            incident_dict["end_time"] = "Still open"

        template_context = {
            "title": title,
            "event": event,
            "incident_dict": incident_dict,
        }
        subject = f"{settings.NOTIFICATION_SUBJECT_PREFIX}{title}"
        message = render_to_string("notificationprofile/apprise.txt", template_context)

        return subject, message

    @classmethod
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], notify_type=None, **_) -> bool:
        """
        Sends an Apprise notification about a given event to the given destinations

        Returns False if no destinations were given and
        True if notifications were sent
        """
        if not are_notifications_enabled():
            LOG.info("notifications: turned off sitewide, not sending")
            return False

        destinations = cls.get_relevant_destinations(destinations)
        if not destinations:
            return False

        if Apprise is None:
            LOG.error("The 'apprise' package is not installed")
            return False

        # Note that Apprise automatically leaves out 'subject' for destinations that don't support it
        subject, message = cls.create_message_context(event=event)
        failed = 0
        num_destinations = len(destinations)
        for destination in destinations:
            destination_url = cls.get_relevant_address(destination)

            notifier = Apprise()
            notifier.add(destination_url)

            kwargs = {"body": message, "title": subject}
            if notify_type is not None:
                kwargs["notify_type"] = notify_type
            result = notifier.notify(**kwargs)

            if not result:
                failed += 1
                LOG.error("Apprise: Failed to send event #%i to destination #%i", event.pk, destination.pk)
            else:
                LOG.debug("Apprise: Sent event #%i to destination #%i", event.pk, destination.pk)

        if failed:
            if num_destinations == failed:
                LOG.error("Apprise: Failed to send event #%i to any destinations", event.pk)
                return False
            LOG.warning(
                "Apprise: Failed to send event #%i to %i of %i destinations",
                event.pk,
                failed,
                num_destinations,
            )
        return True
