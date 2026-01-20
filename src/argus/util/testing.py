from django.db.models.signals import post_save

from argus.incident.signals import send_notification
from argus.incident.signals import background_send_notification
from argus.incident.signals import add_planned_maintenance_tasks_covering_incident
from argus.incident.models import Event, Incident


__all__ = [
    "disconnect_signals",
    "connect_signals",
]


# Signals that close the database connection, interferes with some tests


def disconnect_signals():
    post_save.disconnect(send_notification, Event, dispatch_uid="send_notification")
    post_save.disconnect(background_send_notification, Event, dispatch_uid="send_notification")
    post_save.disconnect(add_planned_maintenance_tasks_covering_incident, Incident)


def connect_signals():
    post_save.connect(send_notification, Event, dispatch_uid="send_notification")
    post_save.connect(background_send_notification, Event, dispatch_uid="send_notification")
    post_save.connect(add_planned_maintenance_tasks_covering_incident, Incident)
