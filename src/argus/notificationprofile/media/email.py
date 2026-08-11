from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from argus.incident.models import Event
from .base import NotificationMedium, modelinstance_to_dict
from ..models import DestinationConfig
from ..utils import are_notifications_enabled
from argus.util.datetime_utils import INFINITY, LOCAL_INFINITY

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.contrib.auth import get_user_model

    User = get_user_model()

LOG = logging.getLogger(__name__)

__all__ = [
    "send_email_safely",
    "EmailNotification",
]


def send_email_safely(function, additional_error=None, *args, **kwargs) -> int:
    try:
        result = function(*args, **kwargs)
        return result
    except ConnectionRefusedError:
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
    MEDIA_NAME = "Email"
    MEDIA_SETTINGS_KEY = "email_address"
    MEDIA_JSON_SCHEMA = {
        "title": "Email Settings",
        "description": "Settings for a DestinationConfig using email.",
        "type": "object",
        "required": [MEDIA_SETTINGS_KEY],
        "properties": {
            MEDIA_SETTINGS_KEY: {
                "type": "string",
                "title": "Email address",
            },
        },
    }

    class Form(forms.Form):
        email_address = forms.EmailField()

    @staticmethod
    def create_message_context(event: Event):
        """Creates the subject, message and html message for the email"""
        title = f"{event}"
        incident_dict = modelinstance_to_dict(event.incident)
        for field in ("id", "source_id"):
            incident_dict.pop(field)
        incident_dict["details_url"] = event.incident.pp_details_url()
        if event.incident.end_time in {INFINITY, LOCAL_INFINITY}:
            incident_dict["end_time"] = "Still open"

        template_context = {
            "title": title,
            "event": event,
            "incident_dict": incident_dict,
        }
        subject = f"{settings.NOTIFICATION_SUBJECT_PREFIX}{title}"
        message = render_to_string("notificationprofile/email.txt", template_context)
        html_message = render_to_string("notificationprofile/email.html", template_context)

        return subject, message, html_message

    @classmethod
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], **_) -> bool:
        """
        Sends email about a given event to the given email destinations

        Returns False if no email destinations were given and
        True if emails were sent
        """
        if not are_notifications_enabled():
            LOG.info("notifications: turned off sitewide, not sending")
            return False

        destinations = cls.get_relevant_destinations(destinations)
        if not destinations:
            return False

        subject, message, html_message = cls.create_message_context(event=event)
        failed = 0
        num_destinations = len(destinations)
        for destination in destinations:
            email_address = cls.get_relevant_address(destination)
            sent = send_email_safely(
                send_mail,
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[email_address],
                html_message=html_message,
            )
            if not sent:
                failed += 1
                LOG.error("Email: Failed to send event #%i to destination #%i", event.pk, destination.pk)
            else:
                LOG.debug("Email: Sent event #%i to destination #%i", event.pk, destination.pk)

        if failed:
            if num_destinations == failed:
                LOG.error("Email: Failed to send to any addresses")
                return False
            LOG.warn(
                "Email: Failed to send to %i of %i addresses",
                failed,
                num_destinations,
            )
        return True
