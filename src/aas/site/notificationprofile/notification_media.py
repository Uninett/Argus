import logging
from abc import ABC, abstractmethod
from typing import Type

from django.conf import settings
from django.template.loader import render_to_string

from aas.site.alert.models import Alert
from aas.site.alert.serializers import AlertSerializer
from aas.site.auth.models import User
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
            logging.getLogger('django.request').warning(
                f"Cannot send email notification to user '{user}', as they have not set an email address."
            )

        title = f"Alert at {alert}"
        alert_dict = AlertSerializer(alert).data
        # TODO: remove pk from serialization instead?
        alert_dict.pop('pk')

        template_context = {
            'title':              title,
            'alert_dict':         alert_dict,
            'longest_field_name_length': len(max(alert_dict, key=len)),
        }
        user.email_user(
            subject=f"{settings.NOTIFICATION_SUBJECT_PREFIX}{title}",
            message=render_to_string("notificationprofile/email.txt", template_context),
            html_message=render_to_string("notificationprofile/email.html", template_context),
        )


MODEL_REPRESENTATION_TO_CLASS = {
    NotificationProfile.EMAIL: EmailNotification,
    NotificationProfile.SMS:   None,
    NotificationProfile.SLACK: None,
}


def get_medium(model_representation: str) -> Type[NotificationMedium]:
    return MODEL_REPRESENTATION_TO_CLASS[model_representation]
