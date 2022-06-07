from django.db.models import Q
from django.utils import timezone
from rest_framework.authtoken.models import Token

from argus.incident.models import get_or_create_default_instances, Incident, Tag
from argus.notificationprofile.media import background_send_notifications_to_users
from .models import SourceSystem, Incident, Event, Acknowledgement


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


def close_token_incident(sender, instance: Token, *args, **kwargs):
    if not hasattr(instance.user, "source_system"):
        return

    argus_user, _, source_system = get_or_create_default_instances()
    tags = Tag.objects.filter(
        (Q(key="problem_type") & Q(value="token_expiry"))
        | (Q(key="source_system") & Q(value=instance.user.source_system))
    )
    open_incidents = Incident.objects.open().filter(source_id=source_system.id)
    for tag in tags:
        open_incidents = open_incidents.filter(incident_tag_relations__tag=tag)
    closing_events = [
        Event(
            incident=incident,
            actor=argus_user,
            timestamp=timezone.now(),
            type="END",
            description=incident.description,
        )
        for incident in open_incidents
    ]
    for incident in open_incidents:
        incident.end_time = timezone.now()
        incident.save(update_fields=["end_time"])
    Event.objects.bulk_create(closing_events)
