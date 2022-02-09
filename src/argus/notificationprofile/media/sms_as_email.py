"""A notification medium implementation for an email-to-SMS Gateway.

This SMS gateway has an email specific interface. The email subject must contain the
recipient's phone number. The email body must contain the message text.
"""
import logging
from typing import List

from django.conf import settings
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from ...incident.models import Event
from ..models import DestinationConfig
from .base import NotificationMedium
from .email import send_email_safely

LOG = logging.getLogger(__name__)


class SMSNotification(NotificationMedium):
    MEDIA_SLUG = "sms"

    @staticmethod
    def validate(sms_dict, instance, context):
        if not list(sms_dict["settings"].keys()) == ["phone_number"]:
            raise ValidationError("Incorrect settings format. Only enter a phone number.")

    @staticmethod
    def send(event: Event, destinations: List[DestinationConfig], **kwargs):
        recipient = getattr(settings, "SMS_GATEWAY_ADDRESS", None)
        if not recipient:
            LOG.error("SMS_GATEWAY_ADDRESS is not set, cannot dispatch SMS notifications using this plugin")
            return

        sms_destinations = destinations.filter(media__slug=SMSNotification.MEDIA_SLUG)
        if not sms_destinations:
            return False
        phone_numbers = [destination.settings["phone_numbers"] for destination in sms_destinations]
        title = f"{event.description}"
        for phone_number in phone_numbers:
            send_email_safely(
                send_mail, subject=f"sms {phone_number}", message=title, from_email=None, recipient_list=[recipient]
            )

        return True
