"""A notification medium implementation for an email-to-SMS Gateway.

This SMS gateway has an email specific interface. The email subject must contain the
recipient's phone number. The email body must contain the message text.
"""
import logging

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.query import QuerySet
from phonenumber_field.formfields import PhoneNumberField
from rest_framework.exceptions import ValidationError

from ...incident.models import Event
from ..models import DestinationConfig
from .base import NotificationMedium
from .email import send_email_safely

LOG = logging.getLogger(__name__)


class SMSNotification(NotificationMedium):
    MEDIA_SLUG = "sms"
    MEDIA_NAME = "SMS"

    class PhoneNumberForm(forms.Form):
        phone_number = PhoneNumberField()

    @classmethod
    def validate(cls, instance, sms_dict):
        form = cls.PhoneNumberForm(sms_dict["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)

        form.cleaned_data["phone_number"] = form.cleaned_data["phone_number"].as_e164

        return form.cleaned_data

    @classmethod
    def get_label(self, destination):
        return destination.settings.get("phone_number")

    @staticmethod
    def send(event: Event, destinations: QuerySet[DestinationConfig], **kwargs):
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
