from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from argus.incident.models import Incident, ActiveIncident
from argus.incident.serializers import IncidentSerializer

SUBSCRIBED_ACTIVE_INCIDENTS = "subscribed_active_incidents"

def _notify_on_change_or_create(sender, instance: Incident, created: bool, raw: bool, *args, deleted=False, **kwargs):
    is_new = created or raw
    type_str = "deleted" if deleted else ("created" if is_new else "modified")

    serializer = IncidentSerializer(instance)
    channel_layer = get_channel_layer()
    content = {
        "type": type_str,
        "payload": serializer.data,
    }
    async_to_sync(channel_layer.group_send)(SUBSCRIBED_ACTIVE_INCIDENTS, {
        "type": "notify",
        "content": content,
    })

@receiver(post_save, sender=Incident)
def notify_on_incident_change_or_create(sender, instance: Incident, *args, **kwargs):
    _notify_on_change_or_create(sender, instance, *args, **kwargs)

@receiver(post_save, sender=ActiveIncident)
def notify_on_incident_change_or_create(sender, instance: ActiveIncident, *args, **kwargs):
    _notify_on_change_or_create(sender, instance.incident, *args,**kwargs)

@receiver(post_delete, sender=ActiveIncident)
def notify_on_incident_delete(sender, instance: ActiveIncident, *args, **kwargs):
    _notify_on_change_or_create(sender, instance.incident, False, False, *args, deleted=True, **kwargs)
