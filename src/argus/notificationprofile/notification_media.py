import json
import logging
from abc import ABC, abstractmethod
from typing import List

from django.conf import settings
from django.template.loader import render_to_string
from rest_framework.renderers import JSONRenderer

from argus.incident.models import Alert
from argus.incident.serializers import AlertSerializer
from argus.auth.models import User
from .models import NotificationProfile


class NotificationMedium(ABC):
    @staticmethod
    @abstractmethod
    def send(alert: Alert, user: User):
        pass


class EmailNotification(NotificationMedium):
    @staticmethod
    def send(alert, user):
        if not user.email:
            logging.getLogger("django.request").warning(
                f"Cannot send email notification to user '{user}', as they have not set an email address."
            )

        title = f"Alert at {alert}"
        alert_dict = AlertSerializer(
            alert, context={AlertSerializer.NO_PKS_KEY: True}
        ).data
        # Convert OrderedDicts to dicts
        alert_dict = json.loads(JSONRenderer().render(alert_dict))

        template_context = {
            "title": title,
            "alert_dict": alert_dict,
            "longest_field_name_length": len(max(alert_dict, key=len)),
        }
        user.email_user(
            subject=f"{settings.NOTIFICATION_SUBJECT_PREFIX}{title}",
            message=render_to_string("notificationprofile/email.txt", template_context),
            html_message=render_to_string(
                "notificationprofile/email.html", template_context
            ),
        )


MODEL_REPRESENTATION_TO_CLASS = {
    NotificationProfile.EMAIL: EmailNotification,
    NotificationProfile.SMS: None,
    NotificationProfile.SLACK: None,
}


def send_notifications_to_users(alert: Alert):
    # TODO: only send one notification per medium per user
    for profile in NotificationProfile.objects.select_related("user"):
        if profile.alert_fits(alert):
            send_notification(profile.user, profile, alert)


def send_notification(user: User, profile: NotificationProfile, alert: Alert):
    media = get_notification_media(list(profile.media))
    for medium in media:
        if medium is not None:
            medium.send(alert, user)


def get_notification_media(model_representations: List[str]):
    return (
        MODEL_REPRESENTATION_TO_CLASS[representation]
        for representation in model_representations
    )
