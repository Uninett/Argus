import json
import logging
from abc import ABC, abstractmethod
from multiprocessing import Process
from typing import List

from django.conf import settings
from django.db import connections
from django.template.loader import render_to_string
from rest_framework.renderers import JSONRenderer

from argus.auth.models import User
from argus.incident.models import Incident
from argus.incident.serializers import IncidentSerializer
from .models import NotificationProfile


LOG = logging.getLogger(__name__)


class NotificationMedium(ABC):
    @staticmethod
    @abstractmethod
    def send(incident: Incident, user: User):
        pass


class EmailNotification(NotificationMedium):
    @staticmethod
    def send(incident, user):
        if not user.email:
            logging.getLogger("django.request").warning(
                f"Cannot send email notification to user '{user}', as they have not set an email address."
            )

        title = f"Incident at {incident}"
        incident_dict = IncidentSerializer(incident, context={IncidentSerializer.NO_PKS_KEY: True}).data
        # Convert OrderedDicts to dicts
        incident_dict = json.loads(JSONRenderer().render(incident_dict))

        template_context = {
            "title": title,
            "incident_dict": incident_dict,
            "longest_field_name_length": len(max(incident_dict, key=len)),
        }
        try:
            user.email_user(
                subject=f"{settings.NOTIFICATION_SUBJECT_PREFIX}{title}",
                message=render_to_string("notificationprofile/email.txt", template_context),
                html_message=render_to_string("notificationprofile/email.html", template_context),
            )
        except ConnectionRefusedError as e:
            EMAIL_HOST = getattr(settings, "EMAIL_HOST", None)
            if not EMAIL_HOST:
                LOG.error("Notification: Email: EMAIL_HOST not set, cannot send")
            EMAIL_PORT = getattr(settings, "EMAIL_PORT", None)
            if not EMAIL_PORT:
                LOG.error("Notification: Email: EMAIL_PORT not set, cannot send")
            if EMAIL_HOST and EMAIL_PORT:
                LOG.error("Notification: Email: Connection refused to \"%s\", port \"%s\"", EMAIL_HOST, EMAIL_PORT)
            # TODO: Store error as incident


MODEL_REPRESENTATION_TO_CLASS = {
    NotificationProfile.Media.EMAIL: EmailNotification,
    NotificationProfile.Media.SMS: None,
    NotificationProfile.Media.SLACK: None,
}


def send_notifications_to_users(incident: Incident):
    if not getattr(settings, "SEND_NOTIFICATIONS", False):
        LOG.info("Notification: turned off sitewide, not sending for \"%s\"", incident)
        return
    # TODO: only send one notification per medium per user
    LOG.info("Notification: sending incident \"%s\"", incident)
    for profile in NotificationProfile.objects.select_related("user"):
        if profile.incident_fits(incident):
            send_notification(profile.user, profile, incident)
    else:
        LOG.info("Notification: no listeners for \"%s\"", incident)
        return
    LOG.info("Notification: incident \"%s\" sent!", incident)


def background_send_notifications_to_users(incident: Incident):
    connections.close_all()
    LOG.info("Notification: backgrounded: about to send incident \"%s\"", incident)
    p = Process(target=send_notifications_to_users, args=(incident,))
    p.start()
    return p


def send_notification(user: User, profile: NotificationProfile, incident: Incident):
    media = get_notification_media(profile.media)
    for medium in media:
        if medium is not None:
            medium.send(incident, user)
    else:
        LOG.warn("Notification: Could not send notification, nowhere to send it to")


def get_notification_media(model_representations: List[str]):
    # This will never be a long list
    media = [MODEL_REPRESENTATION_TO_CLASS[representation]
             for representation in model_representations
             if MODEL_REPRESENTATION_TO_CLASS[representation]]
    if media:
        return media
    LOG.error("Notification: nowhere to send notifications!")
    # TODO: Store error as incident
    return ()
