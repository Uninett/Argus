import logging
from typing import List

from argus.incident.models import Event
from django.conf import settings
from django.core.mail import send_mail
from django import forms
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

from ..models import DestinationConfig
from .base import NotificationMedium

LOG = logging.getLogger(__name__)

__all__ = [
    "send_email_safely",
    "EmailNotification",
]


def modelinstance_to_dict(obj):
    dict_ = vars(obj).copy()
    dict_.pop("_state")
    return dict_


def send_email_safely(function, additional_error=None, *args, **kwargs):
    try:
        result = function(*args, **kwargs)
        return result
    except ConnectionRefusedError as e:
        EMAIL_HOST = getattr(settings, "EMAIL_HOST", None)
        if not EMAIL_HOST:
            LOG.error("Notification: Email: EMAIL_HOST not set, cannot send")
        EMAIL_PORT = getattr(settings, "EMAIL_PORT", None)
        if not EMAIL_PORT:
            LOG.error("Notification: Email: EMAIL_PORT not set, cannot send")
        if EMAIL_HOST and EMAIL_PORT:
            LOG.error('Notification: Email: Connection refused to "%s", port "%s"', EMAIL_HOST, EMAIL_PORT)
        if additional_error:
            LOG.error(*additional_error)
        # TODO: Store error as incident


class EmailNotification(NotificationMedium):
    MEDIA_SLUG = "email"

    class Form(forms.Form):
        synced = forms.BooleanField(disabled=True, required=False, initial=False)
        email_address = forms.EmailField()

    @classmethod
    def validate(cls, instance, email_dict):
        if instance.instance.settings["synced"]:
            raise ValidationError("Cannot change the default destination.")
        form = cls.Form(email_dict["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)
        if form.cleaned_data["email_address"] == instance.context["request"].user.email:
            raise ValidationError("This email address is already saved in the default destination of this user.")

    @staticmethod
    def send(event: Event, destinations: List[DestinationConfig], **_):
        email_destinations = destinations.filter(media__slug=EmailNotification.MEDIA_SLUG)
        if not email_destinations:
            return False

        recipient_list = [destination.settings["email_address"] for destination in email_destinations]
        title = f"{event}"
        incident_dict = modelinstance_to_dict(event.incident)
        for field in ("id", "source_id"):
            incident_dict.pop(field)

        template_context = {
            "title": title,
            "event": event,
            "incident_dict": incident_dict,
        }
        subject = f"{settings.NOTIFICATION_SUBJECT_PREFIX}{title}"
        message = render_to_string("notificationprofile/email.txt", template_context)
        html_message = render_to_string("notificationprofile/email.html", template_context)
        send_email_safely(
            send_mail,
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=recipient_list,
            html_message=html_message,
        )

        return True
