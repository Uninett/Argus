from django.db.models.signals import post_save

from argus.incident.signals import send_notification
from argus.incident.models import Event


__all__ = [
    "disconnect_signals",
    "connect_signals",
]


# Signals that close the database connection, interferes with some tests


def disconnect_signals():
    post_save.disconnect(send_notification, Event, dispatch_uid="send_notification")


def connect_signals():
    post_save.connect(send_notification, Event, dispatch_uid="send_notification")
