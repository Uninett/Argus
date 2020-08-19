import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from argus.incident.models import Incident
from argus.incident.serializers import IncidentSerializer

LOG = logging.getLogger(__name__)
SUBSCRIBED_OPEN_INCIDENTS = "subscribed_open_incidents"


@receiver(post_save, sender=Incident)
def notify_on_change_or_create(sender, instance: Incident, created: bool, raw: bool, *args, **kwargs):
    is_new = created or raw
    type_str = "created" if is_new else "modified"

    serializer = IncidentSerializer(instance)
    channel_layer = get_channel_layer()
    content = {
        "type": type_str,
        "payload": serializer.data,
    }
    try:
        async_to_sync(channel_layer.group_send)(SUBSCRIBED_OPEN_INCIDENTS, {"type": "notify", "content": content})
    except ConnectionRefusedError as error:
        LOG.error("Websockets: Could not push: %s", error)
        # TODO: make a (non-signal inducing incident)
