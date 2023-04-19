from __future__ import annotations

import importlib
import logging
from multiprocessing import Process
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connections

from ..models import NotificationProfile, DestinationConfig
from argus.util.utils import import_class_from_dotted_path

if TYPE_CHECKING:
    from typing import List

    from argus.incident.models import Event  # noqa: Break circular import

    from ..models import DestinationConfig

LOG = logging.getLogger(__name__)


__all__ = [
    "send_notification",
    "background_send_notification",
    "find_destinations_for_event",
    "send_notifications_to_users",
    "get_notification_media",
]


# TODO: Raise Incident if media_class not importable?
MEDIA_PLUGINS = getattr(settings, "MEDIA_PLUGINS")
MEDIA_CLASSES = [import_class_from_dotted_path(media_plugin) for media_plugin in MEDIA_PLUGINS]
MEDIA_CLASSES_DICT = {media_class.MEDIA_SLUG: media_class for media_class in MEDIA_CLASSES}


def send_notification(destinations: List[DestinationConfig], event: Event):
    sent = False
    media = get_notification_media(destinations)
    # Plugin expects queryset...
    ids = (dest.id for dest in destinations)
    qs = DestinationConfig.objects.filter(id__in=ids)
    for medium in media:
        sent = medium.send(event, qs) or sent
    if not sent:
        LOG.warn("Notification: Could not send notification, nowhere to send it to")
        # TODO Store error as incident


def background_send_notification(destinations: List[DestinationConfig], event: Event):
    connections.close_all()
    LOG.info('Notification: backgrounded: about to send event "%s"', event)
    p = Process(target=send_notification, args=(destinations, event))
    p.start()
    return p


def find_destinations_for_event(event: Event):
    destinations = []
    incident = event.incident
    for profile in NotificationProfile.objects.prefetch_related("destinations").select_related("user"):
        LOG.debug('Notification: checking profile "%s"', profile)
        if profile.incident_fits(incident) and profile.event_fits(event):
            destinations.extend(profile.destinations.all())
    if not destinations:
        LOG.info('Notification: no listeners for "%s"', event)
    return destinations


def send_notifications_to_users(event: Event, send=send_notification):
    if not getattr(settings, "SEND_NOTIFICATIONS", False):
        LOG.info('Notification: turned off sitewide, not sending for "%s"', event)
        return
    # TODO: only send one notification per medium per user
    LOG.info('Notification: sending event "%s"', event)
    LOG.debug('Fallback filter set to "%s"', getattr(settings, "ARGUS_FALLBACK_FILTER", {}))
    destinations = find_destinations_for_event(event)
    send(destinations, event)
    LOG.info('Notification: event "%s" sent! %i copies', event, len(destinations))


def get_notification_media(destinations: List[DestinationConfig]):
    destination_slugs = set([destination.media.slug for destination in destinations])
    media = []
    for slug in destination_slugs:
        if slug in MEDIA_CLASSES_DICT.keys():
            media.append(MEDIA_CLASSES_DICT[slug])
        else:
            raise ValueError("Medium %s was not found in imported media.", slug)
    return media
