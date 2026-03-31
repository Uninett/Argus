from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from django.db import transaction

from argus.constants import API_STABLE_VERSION
from argus.notificationprofile.models import DestinationConfig
from argus.notificationprofile.utils import are_notifications_enabled

if TYPE_CHECKING:
    from collections.abc import Iterable

    from types import NoneType

    from django.contrib.auth import get_user_model
    from django.db.models.query import QuerySet

    from argus.incident.models import Event
    from ..serializers import RequestDestinationConfigSerializer

    User = get_user_model()


__all__ = ["NotificationMedium"]
LOG = logging.getLogger(__name__)


class NotificationMedium(ABC):
    class NotDeletableError(Exception):
        """
        Custom exception class that is raised when a destination cannot be
        deleted
        """

    def __init__(self, version: str = API_STABLE_VERSION):
        self.version = version

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
    def get_relevant_address(cls, destination: DestinationConfig) -> Any:
        """
        Returns the "address" to send the message to

        The type of the address depends on the medium, it must be something
        ``cls.send()`` understands.
        """
        raise NotImplementedError

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
        if "label" in validated_data and "settings" not in validated_data:
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
        destination.settings = validated_data.get("settings", destination.settings)
        destination.managed = False
        destination.save()

        if original_destination:
            # finally clone the original destination
            managed_destination = DestinationConfig(**original_destination)
            managed_destination.save()

        return destination
