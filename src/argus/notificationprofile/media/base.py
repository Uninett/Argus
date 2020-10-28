from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argus.incident.models import Event
    from argus.notificationprofile.models import NotificationProfile


__all__ = ["NotificationMedium"]


class NotificationMedium(ABC):
    @staticmethod
    @abstractmethod
    def send(event: Event, profile: NotificationProfile, **kwargs):
        pass
