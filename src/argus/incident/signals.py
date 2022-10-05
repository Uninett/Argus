from argus.notificationprofile.media import background_send_notifications_to_users
from .models import SourceSystem, Incident, Event, Acknowledgement


__all__ = [
    "delete_associated_user",
    "create_first_event",
    "send_notification",
    "delete_associated_event",
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
