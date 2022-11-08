"""A notification medium implementation for an email-to-SMS Gateway.

This SMS gateway has an email specific interface. The email subject must contain the
recipient's phone number. The email body must contain the message text.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from phonenumber_field.formfields import PhoneNumberField
from rest_framework.exceptions import ValidationError

from ...incident.models import Event
from .base import NotificationMedium
from .email import send_email_safely

if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from argus.auth.models import User
    from ..models import DestinationConfig
    from ..serializers import RequestDestinationConfigSerializer

LOG = logging.getLogger(__name__)


class SMSNotification(NotificationMedium):
    MEDIA_SLUG = "sms"
    MEDIA_NAME = "SMS"
    MEDIA_JSON_SCHEMA = {
        "title": "SMS Settings",
        "description": "Settings for a DestinationConfig using SMS.",
        "type": "object",
        "required": ["phone_number"],
        "properties": {
            "phone_number": {
                "type": "string",
                "title": "Phone number",
                "description": "The phone number is validated and the country code needs to be given.",
            }
        },
    }

    class PhoneNumberForm(forms.Form):
        phone_number = PhoneNumberField()

    @classmethod
    def validate(cls, instance: RequestDestinationConfigSerializer, sms_dict: dict, user: User) -> dict:
        """
        Validates the settings of an SMS destination and returns a dict
        with validated and cleaned data
        """
        form = cls.PhoneNumberForm(sms_dict["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)

        form.cleaned_data["phone_number"] = form.cleaned_data["phone_number"].as_e164

        if user.destinations.filter(media_id="sms", settings__phone_number=form.cleaned_data["phone_number"]).exists():
            raise ValidationError({"phone_number": "Phone number already exists"})

        return form.cleaned_data

    @staticmethod
    def get_label(destination: DestinationConfig) -> str:
        """
        Returns the phone number represented by this SMS destination
        """
        return destination.settings.get("phone_number")

    @classmethod
    def has_duplicate(self, queryset: QuerySet, settings: dict) -> bool:
        """
        Returns True if a sms destination with the same phone number
        already exists in the given queryset
        """
        return queryset.filter(settings__phone_number=settings["phone_number"]).exists()

    @staticmethod
    def send(event: Event, destinations: QuerySet[DestinationConfig], **_) -> bool:
        """
        Sends an SMS about a given event to the given sms destinations

        Returns False if no SMS destinations were given and True if SMS were sent
        """
        recipient = getattr(settings, "SMS_GATEWAY_ADDRESS", None)
        if not recipient:
            LOG.error("SMS_GATEWAY_ADDRESS is not set, cannot dispatch SMS notifications using this plugin")
            return

        sms_destinations = destinations.filter(media_id=SMSNotification.MEDIA_SLUG)
        if not sms_destinations:
            return False
        phone_numbers = [destination.settings["phone_number"] for destination in sms_destinations]
        title = f"{event.description}"
        for phone_number in phone_numbers:
            send_email_safely(
                send_mail, subject=f"sms {phone_number}", message=title, from_email=None, recipient_list=[recipient]
            )

        return True
