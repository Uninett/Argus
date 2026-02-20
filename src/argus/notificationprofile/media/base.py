from __future__ import annotations

from django.db import transaction

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from argus.constants import API_STABLE_VERSION
from argus.notificationprofile.models import DestinationConfig

if TYPE_CHECKING:
    from collections.abc import Iterable

    from types import NoneType

    from django.contrib.auth import get_user_model
    from django.db.models.query import QuerySet

    from argus.incident.models import Event
    from ..serializers import RequestDestinationConfigSerializer

    User = get_user_model()


__all__ = ["NotificationMedium"]


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
        Raises a NotDeletableError if the given destination cannot be deleted

        Potential reasons:

        * it is marked as "managed", which means it is usable but read-only for end-users
        * it is in use by at least one notification profiles
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

        If the destination is marked as managed, a copy of the original will be
        made before changing the destination.
        """
        if destination.managed:
            managed_destination = DestinationConfig(
                user=destination.user,
                media_id=destination.media_id,
                settings=destination.settings,
                managed=True,
            )
            managed_destination.save()
        destination.settings = validated_data["settings"]
        destination.managed = False
        DestinationConfig.objects.bulk_update([destination], fields=["settings"])
        return destination
