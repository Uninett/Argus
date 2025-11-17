from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

    from types import NoneType

    from django.contrib.auth import get_user_model
    from django.db.models.query import QuerySet

    from argus.incident.models import Event
    from ..models import DestinationConfig
    from ..serializers import RequestDestinationConfigSerializer

    User = get_user_model()


__all__ = ["NotificationMedium"]


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
