from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

from argus.constants import API_STABLE_VERSION
from argus.incident.models import Event
from .base import NotificationMedium
from ..models import DestinationConfig
from argus.util.datetime_utils import INFINITY, LOCAL_INFINITY

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.contrib.auth import get_user_model
    from django.db.models.query import QuerySet

    from ..serializers import RequestDestinationConfigSerializer

    User = get_user_model()

LOG = logging.getLogger(__name__)

__all__ = [
    "send_email_safely",
    "EmailNotification",
]


def modelinstance_to_dict(obj):
    dict_ = vars(obj).copy()
    dict_.pop("_state")
    return dict_


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
    MEDIA_JSON_SCHEMA = {
        "title": "Email Settings",
        "description": "Settings for a DestinationConfig using email.",
        "type": "object",
        "required": ["email_address"],
        "properties": {"email_address": {"type": "string", "title": "Email address"}},
    }

    class FormV3(forms.Form):
        email_address = forms.EmailField()

    class FormV2(forms.Form):
        synced = forms.BooleanField(disabled=True, required=False, initial=False)
        email_address = forms.EmailField()

    def __init__(self, version: str = API_STABLE_VERSION):
        super().__init__(version)
        if version == "v2":
            self.Form = self.FormV2
        else:
            self.Form = self.FormV3

    def validate(self, instance: RequestDestinationConfigSerializer, email_dict: dict, user: User) -> dict:
        """
        Validates the settings of an email destination and returns a dict
        with validated and cleaned data
        """
        form = self.Form(email_dict["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)
        if form.cleaned_data["email_address"] == instance.context["request"].user.email:
            raise ValidationError("This email address is already registered in another destination.")
        if user.destinations.filter(
            media_id="email", settings__email_address=form.cleaned_data["email_address"]
        ).exists():
            raise ValidationError({"email_address": "Email address already exists"})

        return form.cleaned_data

    @staticmethod
    def get_label(destination: DestinationConfig) -> str:
        """
        Returns the e-mail address represented by this destination
        """
        return destination.settings.get("email_address")

    @classmethod
    def has_duplicate(cls, queryset: QuerySet, settings: dict) -> bool:
        """
        Returns True if an email destination with the same email address
        already exists in the given queryset
        """
        return queryset.filter(settings__email_address=settings["email_address"]).exists()

    @classmethod
    def get_relevant_address(cls, destination: DestinationConfig) -> Any:
        """Returns an email address the message should be sent to"""
        return destination.settings["email_address"]

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
