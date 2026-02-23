from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import TYPE_CHECKING, Any

from rest_framework.exceptions import ValidationError

from apprise import Apprise

from django import forms
from django.conf import settings
from django.template.loader import render_to_string

from argus.incident.models import Event
from ..models import DestinationConfig
from argus.util.datetime_utils import INFINITY, LOCAL_INFINITY

if TYPE_CHECKING:
    from collections.abc import Iterable

    from types import NoneType

    from django.contrib.auth import get_user_model
    from django.db.models.query import QuerySet

    from ..serializers import RequestDestinationConfigSerializer

    User = get_user_model()


__all__ = ["NotificationMedium"]

LOG = logging.getLogger(__name__)


def modelinstance_to_dict(obj):
    dict_ = vars(obj).copy()
    dict_.pop("_state")
    return dict_


class NotificationMedium(ABC):
    class NotDeletableError(Exception):
        """
        Custom exception class that is raised when a destination cannot be
        deleted
        """

    @classmethod
    @abstractmethod
    def validate(cls, instance: RequestDestinationConfigSerializer, dict: dict, user: User) -> dict:
        """
        Validates the settings of destination and returns a dict with
        validated and cleaned data
        """
        pass

    @classmethod
    @abstractmethod
    def has_duplicate(cls, queryset: QuerySet, settings: dict) -> bool:
        """
        Returns True if a destination with the given settings already exists
        in the given queryset
        """
        pass

    @staticmethod
    @abstractmethod
    def get_label(destination: DestinationConfig) -> str:
        """
        Returns a descriptive label for this destination.
        """
        pass

    @classmethod
    @abstractmethod
    def get_relevant_address(cls, destination: DestinationConfig) -> Any:
        """
        Returns the "address" to send the message to

        The type of the address depends on the medium, it must be something
        ``cls.send()`` understands.
        """
        pass

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
    @abstractmethod
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], **kwargs) -> bool:
        """
        Sends message about a given event to the given destinations

        Loops over the destinations from ``cls.get_relevant_destinations`` and
        coneverts each destination to a medium-specifoc "address" via
        ``cls.get_relevant_address``.

        Returns a boolean:
        * True: everything ok
        * False: at least one destination failed
        """
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
    def update(destination: DestinationConfig, validated_data: dict) -> DestinationConfig | NoneType:
        """
        Updates a destination in case the normal update function is not
        sufficient and returns the updated destination in that case,
        returns None otherwise
        """
        return None


class AppriseMedium(NotificationMedium):
    MEDIA_SLUG = "apprise"
    MEDIA_NAME = "Apprise"
    MEDIA_JSON_SCHEMA = {
        "title": "Apprise Settings",
        "description": "Settings for a DestinationConfig using Apprise.",
        "type": "object",
        "required": ["destination_url"],
        "properties": {"destination_url": {"type": "string", "title": "Apprise destination url"}},
    }

    class Form(forms.Form):
        destination_url = forms.URLField()

    def validate(cls, instance: RequestDestinationConfigSerializer, apprise_dict: dict, user: User) -> dict:
        """
        Validates the settings of an apprise destination and returns a dict
        with validated and cleaned data
        """
        form = cls.Form(apprise_dict["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)
        if user.destinations.filter(
            media_id="apprise", settings__destination_url=form.cleaned_data["destination_url"]
        ).exists():
            raise ValidationError({"destination_url": "Webhook already exists"})

        return form.cleaned_data

    @classmethod
    def has_duplicate(cls, queryset: QuerySet, settings: dict) -> bool:
        """
        Returns True if an Apprise destination with the same destination url
        already exists in the given queryset
        """
        return queryset.filter(settings__destination_url=settings["destination_url"]).exists()

    @staticmethod
    def get_label(destination: DestinationConfig) -> str:
        """
        Returns the apprise destination url represented by this destination
        """
        return destination.settings.get("destination_url")

    @classmethod
    def get_relevant_address(cls, destination: DestinationConfig) -> Any:
        """Returns the apprise destination url the message should be sent to"""
        return destination.settings["destination_url"]

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
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], **_) -> bool:
        """
        Sends an Apprise notification about a given event to the given destinations

        Returns False if no destinations were given and
        True if notifications were sent
        """
        destinations = cls.get_relevant_destinations(destinations)
        if not destinations:
            return False

        # Note that Apprise automatically leaves out 'subject' for destinations that don't support it
        subject, message = cls.create_message_context(event=event)
        failed = 0
        num_destinations = len(destinations)
        for destination in destinations:
            destination_url = cls.get_relevant_address(destination)

            notifier = Apprise()
            notifier.add(destination_url)

            result = notifier.notify(body=message, title=subject)

            if not result:
                failed += 1
                LOG.error("Apprise: Failed to send event #%i to destination #%i", event.pk, destination.pk)
            else:
                LOG.debug("Apprise: Sent event #%i to destination #%i", event.pk, destination.pk)

        if failed:
            if num_destinations == failed:
                LOG.error("Apprise: Failed to send to any destinations")
                return False
            LOG.warn(
                "Apprise: Failed to send to %i of %i destinations",
                failed,
                num_destinations,
            )
        return True
