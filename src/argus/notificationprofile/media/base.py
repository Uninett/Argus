from abc import ABC, abstractmethod

from argus.auth.models import User
from argus.incident.models import Incident


__all__ = ['NotificationMedium']


class NotificationMedium(ABC):
    @staticmethod
    @abstractmethod
    def send(incident: Incident, user: User, **kwargs):
        pass
