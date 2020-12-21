"""A notification medium implementation for an email-to-SMS Gateway.

This SMS gateway has an email specific interface. The email subject must contain the
recipient's phone number. The email body must contain the message text.
"""
import logging

from django.core.mail import send_mail
from django.conf import settings

from .base import NotificationMedium
from ..models import NotificationProfile
from ...incident.models import Event
from .email import send_email_safely

LOG = logging.getLogger(__name__)


class SMSNotification(NotificationMedium):
    @staticmethod
    def send(event: Event, profile: NotificationProfile, **kwargs):
        recipient = getattr(settings, "SMS_GATEWAY_ADDRESS", None)
        if not recipient:
            LOG.error("SMS_GATEWAY_ADDRESS is not set, cannot dispatch SMS notifications using this plugin")
            return

        if not profile.phone_number:
            LOG.warning(
                "Cannot send SMS notification to user %s, as no phone number was set in their notification profile",
                profile.user,
            )
            return
        else:
            phone_number = profile.phone_number.phone_number

        title = f"{event.description}"
        LOG.debug("Sending SMS notification to %s on %s", profile.user, phone_number)
        send_email_safely(
            send_mail, subject=f"sms {phone_number}", message=title, from_email=None, recipient_list=[recipient]
        )
