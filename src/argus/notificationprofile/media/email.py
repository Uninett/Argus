from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from argus.incident.models import Event
from argus.util.datetime_utils import INFINITY, LOCAL_INFINITY

from .base import NotificationMedium
from ..models import DestinationConfig

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.contrib.auth import get_user_model

    User = get_user_model()


LOG = logging.getLogger(__name__)

__all__ = [
    "modelinstance_to_dict",
    "send_email_safely",
    "BaseEmailNotification",
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


class BaseEmailNotification(NotificationMedium):
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
        email_addresses = cls.get_relevant_destination_settings(destinations=destinations)
        if not email_addresses:
            return False
        num_emails = len(email_addresses)

        subject, message, html_message = cls.create_message_context(event=event)

        failed = set()
        for email_address in email_addresses:
            sent = send_email_safely(
                send_mail,
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[email_address],
                html_message=html_message,
            )
            if not sent:  # 0 for failure otherwise 1
                failed.add(email_address)

        if failed:
            if num_emails == len(failed):
                LOG.error("Email: Failed to send to any addresses")
                return False
            LOG.warn(
                "Email: Failed to send to %i of %i addresses",
                len(failed),
                num_emails,
            )
            LOG.debug("Email: Failed to send to:", " ".join(failed))
        return True


class EmailNotification(BaseEmailNotification):
    class Form(forms.Form):
        synced = forms.BooleanField(disabled=True, required=False, initial=False)
        email_address = forms.EmailField()

    @classmethod
    def is_not_deletable(cls, destination: DestinationConfig) -> dict[str, Any]:
        """
        Flag if the destination is undeletable due to being defined by an outside source.
        """
        errors = super().is_not_deletable(destination)
        if destination.settings.get("synced", None):
            errors["synced"] = "Email address is read-only, it is defined by an outside source."
        return errors

    @classmethod
    def _clone_if_changing_email_address(cls, destination: DestinationConfig, validated_data: dict):
        """Clone synced destination"""
        if not destination.settings.get("synced", None):
            LOG.warn('Email destination %s does not have "synced" flag in its settings', destination.id)
            return False

        new_address = validated_data["settings"][cls.MEDIA_SETTINGS_KEY]
        old_address = destination.settings[cls.MEDIA_SETTINGS_KEY]
        if new_address == old_address:  # address wasn't changed
            return False

        settings = {
            "synced": True,
            cls.MEDIA_SETTINGS_KEY: old_address,
        }
        DestinationConfig.objects.create(
            user=destination.user,
            media_id=destination.media_id,
            settings=settings,
            label=cls.get_label(destination),
        )
        LOG.info("Cloning synced email-address on update: %s", old_address)
        return True

    @classmethod
    def clean(cls, form: forms.Form, instance: DestinationConfig = None) -> forms.Form:
        synced = False
        if instance:
            # CYA. The admin currently do no validation of destinations created
            synced = instance.settings.get("synced", False)
        form.cleaned_data["synced"] = form.cleaned_data.get("synced", synced)
        return form

    @classmethod
    def update(cls, destination: DestinationConfig, validated_data: dict) -> DestinationConfig:
        """
        Preserves a synced email destination by cloning its contents to
        a new destination and updating the given destination with the given
        validated data and returning the updated destination

        This way the synced destination is not lost
        """
        cls._clone_if_changing_email_address(destination, validated_data)

        # We cannot use super() here since this is not an instance method
        instance = cls._update_destination(destination, validated_data)
        instance.settings["synced"] = False

        instance.save()
        return instance
