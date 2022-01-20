from __future__ import annotations

import importlib
import logging
from multiprocessing import Process
from typing import List, TYPE_CHECKING

from django.conf import settings
from django.db import connections

from ..models import NotificationMedia, NotificationProfile

if TYPE_CHECKING:
    from argus.incident.models import Event  # noqa: Break circular import

LOG = logging.getLogger(__name__)


__all__ = [
    "send_notifications_to_users",
    "background_send_notifications_to_users",
    "send_notification",
    "get_notification_media",
]

# Poor mans's plugins
MEDIA_CLASSES = {}


def _import_class_from_dotted_path(dotted_path: str):
    module_name, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    return class_


def _create_media_classes_if_empty():
    if not MEDIA_CLASSES:
        for media in NotificationMedia.objects.all():
            if media.slug == "email":
                MEDIA_CLASSES[media.slug] = getattr(
                    settings, "DEFAULT_EMAIL_MEDIA", "argus.notificationprofile.media.email.EmailNotification"
                )
            else:
                dotted_path = getattr(settings, "DEFAULT_" + media.name.upper() + "_MEDIA", None)
                if dotted_path and isinstance(dotted_path, str):
                    MEDIA_CLASSES[media.slug] = dotted_path

        for media_type, media_class in MEDIA_CLASSES.items():
            # TODO: Raise Incident if media_class not importable
            MEDIA_CLASSES[media_type] = _import_class_from_dotted_path(media_class)


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
            send_notification(profile, event)
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


def send_notification(profile: NotificationProfile, event: Event):
    media = get_notification_media([medium.slug for medium in profile.media.all()])
    sent = False
    for medium in media:
        medium.send(event, profile)
        sent = True
    if not sent:
        LOG.warn("Notification: Could not send notification, nowhere to send it to")


def get_notification_media(model_representations: List[str]):
    # This will never be a long list
    # fmt:off
    _create_media_classes_if_empty()
    media = [
        MEDIA_CLASSES[representation]
        for representation in model_representations
        if representation in MEDIA_CLASSES
    ]
    # fmt: on
    if media:
        return media
    LOG.error("Notification: nowhere to send notifications!")
    # TODO: Store error as incident
    return ()
