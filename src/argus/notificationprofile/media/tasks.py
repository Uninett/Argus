from django_tasks import task

from argus.incident.models import Event
from argus.notificationprofile.models import DestinationConfig

from . import find_destinations_for_event, send_notification


@task
def task_send_notifications(event_id, destination_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return

    try:
        destination = DestinationConfig.objects.get(id=destination_id)
    except DestinationConfig.DoesNotExist:
        return

    send_notification([destination], event)


@task
def task_check_for_notifications(event_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return

    destinations = find_destinations_for_event(event)
    if not destinations:
        return

    for destination in destinations:
        task_send_notifications.enqueue(event_id, destination.id)
