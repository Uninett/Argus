from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argus.incident.models import Event
    from argus.notificationprofile.models import DestinationConfig, NotificationProfile


__all__ = ["NotificationMedium"]


class NotificationMedium(ABC):
    @classmethod
    @abstractmethod
    def validate(cls, instance, dict):
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
