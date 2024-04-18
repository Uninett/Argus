from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sys

    if sys.version_info[:2] < (3, 9):
        from typing import Iterable
    else:
        from collections.abc import Iterable

    from types import NoneType
    from typing import Union, Set
    from django.db.models.query import QuerySet
    from argus.auth.models import User
    from argus.incident.models import Event
    from ..models import DestinationConfig
    from ..serializers import RequestDestinationConfigSerializer


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
    def get_relevant_addresses(cls, destinations: Iterable[DestinationConfig]) -> Set[DestinationConfig]:
        """Returns a set of addresses the message should be sent to"""
        pass

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
