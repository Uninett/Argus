from __future__ import annotations

import logging
from multiprocessing import Process
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connections
from rest_framework.exceptions import ValidationError

from argus.filter import get_filter_backend
from argus.util.utils import import_class_from_dotted_path

from ..models import DestinationConfig, Media, NotificationProfile

if TYPE_CHECKING:
    import sys

    if sys.version_info[:2] < (3, 9):
        from typing import Iterable
    else:
        from collections.abc import Iterable

    from argus.incident.models import Event  # noqa: Break circular import


filter_backend = get_filter_backend()
ComplexFallbackFilterWrapper = filter_backend.ComplexFallbackFilterWrapper

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
    media_count = len(media)
    for event in events:
        LOG.info('Notification: sending event "%s" to %i mediums', event, media_count)
        for medium in media:
            sent = medium.send(event=event, destinations=destinations)
            if sent:
                LOG.info('Notification: sent event "%s" to "%s"', event, medium.MEDIA_SLUG)
            else:
                LOG.warn('Notification: could not send event "%s" to "%s"', event, medium.MEDIA_SLUG)


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
        fw = ComplexFallbackFilterWrapper(profile=profile)
        LOG.debug('Notification: checking profile "%s" (%s) for event "%s"', profile, profile.user.username, event)
        if fw.incident_fits(incident) and fw.event_fits(event):
            destinations.update(profile.destinations.all())
    LOG.info('Notification: found %i listeners for "%s"', len(destinations), event)
    return destinations


def find_destinations_for_many_events(events: Iterable[Event]):
    destinations = dict()
    for event in events:
        found = find_destinations_for_event(event)
        if found:
            destinations[event] = found
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
    all_destinations = find_destinations_for_many_events(events)
    if not all_destinations:
        return
    for event, destinations in all_destinations.items():
        send(destinations, event)
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
