import logging

from django.db.models import Q
from django.utils import timezone

from rest_framework.authtoken.models import Token
from django_q.tasks import async_task

from argus.notificationprofile.media import find_destinations_for_event
from argus.notificationprofile.media import send_notification
from argus.notificationprofile.media import are_notifications_turned_on

from .models import (
    Acknowledgement,
    ChangeEvent,
    Event,
    Incident,
    SourceSystem,
    Tag,
    get_or_create_default_instances,
)


__all__ = [
    "enqueue_event_for_notification",
    "delete_associated_user",
    "send_notification",
    "delete_associated_event",
    "close_token_incident",
]

LOG = logging.getLogger(__name__)


def enqueue_event_for_notification(sender, instance: Event, *args, **kwargs):
    if not are_notifications_turned_on():
        return

    destinations = find_destinations_for_event(instance)
    if destinations:
        LOG.info('Notification: will be sending notification for "%s"', instance)
        async_task(send_notification, destinations, instance, group="notifications")
    else:
        LOG.debug("Notification: no destinations to send notification to")


def delete_associated_user(sender, instance: SourceSystem, *args, **kwargs):
    if hasattr(instance, "user") and instance.user:
        instance.user.delete()


def delete_associated_event(sender, instance: Acknowledgement, *args, **kwargs):
    if hasattr(instance, "event") and instance.event:
        instance.event.delete()


def close_token_incident(instance: Token, **kwargs):
    if not hasattr(instance.user, "source_system"):
        return

    open_expiry_incidents = Incident.objects.open().token_expiry()

    if not open_expiry_incidents:
        return

    argus_user, _, _ = get_or_create_default_instances()
    source_system_tag = Tag.objects.filter(
        (Q(key="source_system_id") & Q(value=instance.user.source_system.id))
    ).first()

    token_expiry_incident = open_expiry_incidents.filter(incident_tag_relations__tag=source_system_tag).first()

    if not token_expiry_incident:
        return

    token_expiry_incident.set_end(actor=argus_user)
