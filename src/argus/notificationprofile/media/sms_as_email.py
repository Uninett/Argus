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

from ...incident.models import Event
from .base import NotificationMedium
from .email import send_email_safely

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.contrib.auth import get_user_model

    from ..models import DestinationConfig

    User = get_user_model()

LOG = logging.getLogger(__name__)


class SMSNotification(NotificationMedium):
    MEDIA_SLUG = "sms"
    MEDIA_NAME = "SMS"
    MEDIA_SETTINGS_KEY = "phone_number"
    MEDIA_JSON_SCHEMA = {
        "title": "SMS Settings",
        "description": "Settings for a DestinationConfig using SMS.",
        "type": "object",
        "required": [MEDIA_SETTINGS_KEY],
        "properties": {
            MEDIA_SETTINGS_KEY: {
                "type": "string",
                "title": "Phone number",
                "description": "The phone number is validated and the country code needs to be given.",
            },
        },
    }

    class Form(forms.Form):
        phone_number = PhoneNumberField()

    @classmethod
    def clean(cls, form: Form, instance: DestinationConfig = None) -> Form:
        form.cleaned_data[cls.MEDIA_SETTINGS_KEY] = form.cleaned_data[cls.MEDIA_SETTINGS_KEY].as_e164
        return form

    @classmethod
    def send(cls, event: Event, destinations: Iterable[DestinationConfig], **_) -> bool:
        """
        Sends an SMS about a given event to the given sms destinations

        Returns False if no SMS destinations were given and True if SMS were sent
        """
        recipient = getattr(settings, "SMS_GATEWAY_ADDRESS", None)
        if not recipient:
            LOG.error("SMS_GATEWAY_ADDRESS is not set, cannot dispatch SMS notifications using this plugin")
            return

        phone_numbers = cls.get_relevant_destination_settings(destinations=destinations)
        if not phone_numbers:
            return False

        # there is only one recipient, so failing to send a single message
        # means something is wrong on the email server
        sent = True
        for phone_number in phone_numbers:
            sent = send_email_safely(
                send_mail,
                subject=f"sms {phone_number}",
                message=f"{event.description}",
                from_email=None,
                recipient_list=[recipient],
            )
            if not sent:
                LOG.error("SMS: Failed to send")
                break

        return sent
