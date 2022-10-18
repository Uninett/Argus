from __future__ import annotations

import importlib
import logging
from multiprocessing import Process
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connections

from ..models import NotificationProfile
from argus.util.utils import import_class_from_dotted_path

if TYPE_CHECKING:
    from typing import List

    from argus.incident.models import Event  # noqa: Break circular import

    from ..models import DestinationConfig

LOG = logging.getLogger(__name__)


__all__ = [
    "send_notifications_to_users",
    "background_send_notifications_to_users",
    "send_notification",
    "get_notification_media",
]


# TODO: Raise Incident if media_class not importable?
MEDIA_PLUGINS = getattr(settings, "MEDIA_PLUGINS")
MEDIA_CLASSES = [import_class_from_dotted_path(media_plugin) for media_plugin in MEDIA_PLUGINS]
MEDIA_CLASSES_DICT = {media_class.MEDIA_SLUG: media_class for media_class in MEDIA_CLASSES}


def send_notifications_to_users(event: Event):
    if not getattr(settings, "SEND_NOTIFICATIONS", False):
        LOG.info('Notification: turned off sitewide, not sending for "%s"', event)
        return
    # TODO: only send one notification per medium per user
    LOG.info('Notification: sending event "%s"', event)
    LOG.debug('Fallback filter set to "%s"', getattr(settings, "ARGUS_FALLBACK_FILTER", {}))
    sent = False
    for profile in NotificationProfile.objects.select_related("user"):
        LOG.debug('Notification: checking profile "%s"', profile)
        if profile.incident_fits(event.incident):
            send_notification(profile.destinations.all(), event)
            sent = True
        LOG.debug('Notification: sent? %s: profile "%s", event "%s"', sent, profile, event)
    if not sent:
        LOG.info('Notification: no listeners for "%s"', event)
        return
    LOG.info('Notification: event "%s" sent!', event)


def background_send_notifications_to_users(event: Event):
    connections.close_all()
    LOG.info('Notification: backgrounded: about to send event "%s"', event)
    p = Process(target=send_notifications_to_users, args=(event,))
    p.start()
    return p


def send_notification(destinations: List[DestinationConfig], event: Event):
    sent = False
    media = get_notification_media(destinations)
    for medium in media:
        sent = medium.send(event, destinations) or sent
    if not sent:
        LOG.warn("Notification: Could not send notification, nowhere to send it to")
        # TODO Store error as incident


def get_notification_media(destinations: List[DestinationConfig]):
    destination_slugs = set([destination.media.slug for destination in destinations])
    media = []
    for slug in destination_slugs:
        if slug in MEDIA_CLASSES_DICT.keys():
            media.append(MEDIA_CLASSES_DICT[slug])
        else:
            raise ValueError("Medium %s was not found in imported media.", slug)
    return media
