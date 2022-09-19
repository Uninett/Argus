from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from django.db.models.query import QuerySet

if TYPE_CHECKING:
    from argus.incident.models import Event
    from argus.notificationprofile.models import DestinationConfig, NotificationProfile


__all__ = ["NotificationMedium"]


class NotificationMedium(ABC):
    @classmethod
    @abstractmethod
    def validate(cls, instance, dict):
        pass

    @classmethod
    @abstractmethod
    def has_duplicate(self, queryset: QuerySet, settings: dict) -> bool:
        """
        Returns True if a destination with the given settings already exists
        in the given queryset
        """
        pass

    @staticmethod
    @abstractmethod
    def get_label(destination: DestinationConfig):
        pass

    @staticmethod
    @abstractmethod
    def send(event: Event, profile: NotificationProfile, **kwargs):
        pass

    @staticmethod
    def is_deletable(destination: DestinationConfig):
        return None

    @staticmethod
    def update(destination, validated_data):
        return None
