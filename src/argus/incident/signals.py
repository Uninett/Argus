from django.db.models import Q
from django.utils import timezone
from rest_framework.authtoken.models import Token

from argus.incident.models import get_or_create_default_instances, Incident
from argus.notificationprofile.media import background_send_notifications_to_users
from .models import Acknowledgement, ChangeEvent, Event, Incident, SourceSystem, Tag


__all__ = [
    "delete_associated_user",
    "create_first_event",
    "send_notification",
    "delete_associated_event",
    "close_token_incident",
]


def delete_associated_user(sender, instance: SourceSystem, *args, **kwargs):
    if hasattr(instance, "user") and instance.user:
        instance.user.delete()


def create_first_event(sender, instance: Incident, created, raw, *args, **kwargs):
    if raw or not created:
        return
    if not instance.start_event and not instance.stateless_event:
        event_type = Event.Type.INCIDENT_START if instance.stateful else Event.Type.STATELESS
        Event.objects.create(
            incident=instance,
            actor=instance.source.user,
            timestamp=instance.start_time,
            type=event_type,
            description=instance.description,
        )


def send_notification(sender, instance: Event, *args, **kwargs):
    background_send_notifications_to_users(instance)


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


def detect_changes(sender, instance: Incident, raw, *args, **kwargs):
    if raw or not instance.id or not instance.end_time:
        return
    instance._changed = {}
    previous = Incident.objects.get(id=instance.id)
    if previous.level != instance.level:
        instance._changed["level"] = previous.level
    if previous.details_url != instance.details_url:
        instance._changed["details_url"] = previous.details_url
    if previous.ticket_url != instance.ticket_url:
        instance._changed["ticket_url"] = previous.ticket_url


def create_change_events(sender, instance: Incident, created, raw, *args, **kwargs):
    if not instance or not getattr(instance, "_changed", None):
        return

    for attr in ("level", "details_url", "ticket_url"):
        if attr not in instance._changed.keys():
            continue

        old_value = instance._changed[attr]
        new_value = getattr(instance, attr)
        description = f"Change: {attr} {old_value} → {new_value}"
        ChangeEvent.objects.create(
            incident=instance, actor=instance.source.user, timestamp=timezone.now(), description=description
        )
