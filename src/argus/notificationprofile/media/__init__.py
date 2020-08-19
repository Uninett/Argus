import importlib
import logging
from multiprocessing import Process
from typing import List

from django.conf import settings
from django.db import connections

from argus.auth.models import User
from argus.incident.models import Incident
from .email import EmailNotification
from ..models import NotificationProfile


LOG = logging.getLogger(__name__)


__all__ = [
    "send_notifications_to_users",
    "background_send_notifications_to_users",
    "send_notification",
    "get_notification_media",
]


# Poor mans's plugins
MEDIA_CLASSES = {
    NotificationProfile.Media.EMAIL: getattr(settings, "DEFAULT_EMAIL_MEDIA", EmailNotification),
    NotificationProfile.Media.SMS: getattr(settings, "DEFAULT_SMS_MEDIA", None),
    NotificationProfile.Media.SLACK: getattr(settings, "DEFAULT_SLACK_MEDIA", None),
}


def _import_class_from_dotted_path(dotted_path: str):
    module_name, class_name = dotted_path.rsplit('.', 1)
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    return class_


for media_type, media_class in MEDIA_CLASSES.items():
    if not media_class or not isinstance(media_class, str):
        continue
    # Dotted paths here!
    # TODO: Raise Incident if media_class not importable
    MEDIA_CLASSES[media_type] = _import_class_from_dotted_path(media_class)


def send_notifications_to_users(incident: Incident):
    if not getattr(settings, "SEND_NOTIFICATIONS", False):
        LOG.info('Notification: turned off sitewide, not sending for "%s"', incident)
        return
    # TODO: only send one notification per medium per user
    LOG.info('Notification: sending incident "%s"', incident)
    for profile in NotificationProfile.objects.select_related("user"):
        if profile.incident_fits(incident):
            send_notification(profile.user, profile, incident)
    else:
        LOG.info('Notification: no listeners for "%s"', incident)
        return
    LOG.info('Notification: incident "%s" sent!', incident)


def background_send_notifications_to_users(incident: Incident):
    connections.close_all()
    LOG.info('Notification: backgrounded: about to send incident "%s"', incident)
    p = Process(target=send_notifications_to_users, args=(incident,))
    p.start()
    return p


def send_notification(user: User, profile: NotificationProfile, incident: Incident):
    media = get_notification_media(profile.media)
    for medium in media:
        if medium is not None:
            medium.send(incident, user, phone_number=profile.phone_number)
    else:
        LOG.warn("Notification: Could not send notification, nowhere to send it to")


def get_notification_media(model_representations: List[str]):
    # This will never be a long list
    media = [
        MEDIA_CLASSES[representation]
        for representation in model_representations
        if MEDIA_CLASSES[representation]
    ]
    if media:
        return media
    LOG.error("Notification: nowhere to send notifications!")
    # TODO: Store error as incident
    return ()
