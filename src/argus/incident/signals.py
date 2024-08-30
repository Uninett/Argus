from django.db.models import Q
from django.utils import timezone
from rest_framework.authtoken.models import Token

from argus.notificationprofile.media import send_notifications_to_users
from argus.notificationprofile.media import background_send_notification
from argus.notificationprofile.media import send_notification
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
    "delete_associated_user",
    "send_notification",
    "delete_associated_event",
    "close_token_incident",
]


def delete_associated_user(sender, instance: SourceSystem, *args, **kwargs):
    if hasattr(instance, "user") and instance.user:
        instance.user.delete()


def task_send_notification(sender, instance: Event, *args, **kwargs):
    send_notifications_to_users(instance)


def task_background_send_notification(sender, instance: Event, *args, **kwargs):
    send_notifications_to_users(instance, send=background_send_notification)


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
