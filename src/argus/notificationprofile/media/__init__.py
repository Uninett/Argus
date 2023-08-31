from __future__ import annotations

import logging
from multiprocessing import Process
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connections
from rest_framework.exceptions import ValidationError

from ..models import DestinationConfig, Media, NotificationProfile
from argus.util.utils import import_class_from_dotted_path

if TYPE_CHECKING:
    import sys

    if sys.version_info[:2] < (3, 9):
        from typing import Iterable
    else:
        from collections.abc import Iterable

    from argus.incident.models import Event  # noqa: Break circular import

LOG = logging.getLogger(__name__)


__all__ = [
    "api_safely_get_medium_object",
    "send_notification",
    "background_send_notification",
    "find_destinations_for_event",
    "find_destinations_for_many_events",
    "send_notifications_to_users",
    "get_notification_media",
]


# TODO: Raise Incident if media_class not importable?
MEDIA_PLUGINS = getattr(settings, "MEDIA_PLUGINS")
MEDIA_CLASSES = [import_class_from_dotted_path(media_plugin) for media_plugin in MEDIA_PLUGINS]
MEDIA_CLASSES_DICT = {media_class.MEDIA_SLUG: media_class for media_class in MEDIA_CLASSES}


def api_safely_get_medium_object(media_slug):
    try:
        obj = MEDIA_CLASSES_DICT[media_slug]
    except KeyError:
        raise ValidationError(f'Medium "{media_slug}" is not installed.')
    return obj


def send_notification(destinations: Iterable[DestinationConfig], *events: Iterable[Event]):
    if not events:
        return
    media = get_notification_media(destinations)
    # Plugin expects queryset...
    ids = (dest.id for dest in destinations)
    qs = DestinationConfig.objects.filter(id__in=ids)
    media_count = len(media)
    for event in events:
        LOG.info('Notification: sending event "%s" to %i mediums', event, media_count)
        for medium in media:
            sent = medium.send(event, qs)
            if sent:
                LOG.info('Notification: sent event "%s" to "%s"', event, medium.MEDIA_SLUG)


def background_send_notification(destinations: Iterable[DestinationConfig], *events: Event):
    connections.close_all()
    LOG.info("Notification: backgrounded: about to send %i events", len(events))
    p = Process(target=send_notification, args=(destinations, *events))
    p.start()
    return p


def find_destinations_for_event(event: Event):
    destinations = set()
    incident = event.incident
    qs = NotificationProfile.objects.filter(active=True)
    for profile in qs.prefetch_related("destinations").select_related("user"):
        LOG.debug('Notification: checking profile "%s" for event "%s"', profile, event)
        if profile.incident_fits(incident) and profile.event_fits(event):
            destinations.update(profile.destinations.all())
    return destinations


def find_destinations_for_many_events(events: Iterable[Event]):
    destinations = set()
    for event in events:
        destinations.update(find_destinations_for_event(event))
    LOG.info('Notification: found %i listeners for "%s"', len(destinations), event)
    return destinations


def send_notifications_to_users(*events: Iterable[Event], send=send_notification):
    if not events:
        LOG.warn("Notification: no events to send, programming error?")
        return
    if not getattr(settings, "SEND_NOTIFICATIONS", False):
        LOG.info("Notification: turned off sitewide, not sending any")
        return
    # TODO: only send one notification per medium per user
    LOG.debug('Fallback filter set to "%s"', getattr(settings, "ARGUS_FALLBACK_FILTER", {}))
    destinations = find_destinations_for_many_events(events)
    if not destinations:
        return
    send(destinations, *events)
    LOG.info("Notification: %i events sent! %i copies", len(events), len(destinations))


def get_notification_media(destinations: Iterable[DestinationConfig]):
    destination_slugs = set([destination.media.slug for destination in destinations])
    media = []
    for slug in destination_slugs:
        if slug in MEDIA_CLASSES_DICT.keys():
            media.append(MEDIA_CLASSES_DICT[slug])
        else:
            LOG.warning("Medium %s was not found in imported media.", slug)
            not_installed_medium = Media.objects.get(slug=slug)
            not_installed_medium.installed = False
            not_installed_medium.save(update_fields=["installed"])
    return media
