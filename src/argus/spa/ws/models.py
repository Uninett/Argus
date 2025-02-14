import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from argus.incident.models import Incident
from argus.incident.serializers import IncidentSerializer
from argus.util.signals import bulk_changed

LOG = logging.getLogger(__name__)
SUBSCRIBED_OPEN_INCIDENTS = "subscribed_open_incidents"


@receiver(post_save, sender=Incident)
def notify_on_change_or_create(sender, instance: Incident, created: bool, raw: bool, *args, **kwargs):
    is_new = created or raw
    send_via_websockets(instance, is_new)


@receiver(bulk_changed, sender=Incident)
def notify_on_bulk(sender, instances, *args, **kwargs):
    is_new = False  # all changed!
    for instance in instances:
        if getattr(instance, "user", None):
            send_via_websockets(instance, is_new)


def send_via_websockets(incident, is_new):
    type_str = "created" if is_new else "modified"

    serializer = IncidentSerializer(incident)
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
