from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

from argus.incident.models import Event
from .base import NotificationMedium
from ..models import DestinationConfig

if TYPE_CHECKING:
    from types import NoneType
    from typing import Union
    from django.db.models.query import QuerySet
    from argus.auth.models import User
    from ..serializers import RequestDestinationConfigSerializer

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
    MEDIA_NAME = "Email"
    MEDIA_JSON_SCHEMA = {
        "title": "Email Settings",
        "description": "Settings for a DestinationConfig using email.",
        "type": "object",
        "required": ["email_address"],
        "properties": {"email_address": {"type": "string", "title": "Email address"}},
    }

    class Form(forms.Form):
        synced = forms.BooleanField(disabled=True, required=False, initial=False)
        email_address = forms.EmailField()

    @classmethod
    def validate(cls, instance: RequestDestinationConfigSerializer, email_dict: dict, user: User) -> dict:
        """
        Validates the settings of an email destination and returns a dict
        with validated and cleaned data
        """
        form = cls.Form(email_dict["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)
        if form.cleaned_data["email_address"] == instance.context["request"].user.email:
            raise ValidationError("This email address is already registered in another destination.")
        if user.destinations.filter(
            media_id="email", settings__email_address=form.cleaned_data["email_address"]
        ).exists():
            raise ValidationError({"email_address": "Email address already exists"})

        return form.cleaned_data

    @classmethod
    def raise_if_not_deletable(cls, destination: DestinationConfig) -> Union[str, NoneType]:
        """
        Raises a NotDeletableError if the given email destination is not able
        to be deleted (if it was defined by an outside source or is in use by
        any notification profiles)
        """
        if destination.settings["synced"]:
            raise cls.NotDeletableError(
                "Cannot delete this email destination since it was defined by an outside source."
            )

        connected_profiles = destination.notification_profiles.all()
        if connected_profiles:
            profiles = ", ".join([str(profile) for profile in connected_profiles])
            raise cls.NotDeletableError(
                f"Cannot delete this destination since it is in use in the notification profile(s): {profiles}."
            )

    @staticmethod
    def update(destination: DestinationConfig, validated_data: dict) -> Union[DestinationConfig, NoneType]:
        """
        Updates the synced email destination by copying its contents to
        a new destination and updating the given destination with the given
        validated data and returning the updated destination

        This way the synced destination is not lost
        """
        if destination.settings["synced"]:
            new_synced_destination = DestinationConfig(
                user=destination.user,
                media_id=destination.media_id,
                settings=destination.settings,
            )
            destination.settings = validated_data["settings"]
            DestinationConfig.objects.bulk_update([destination], fields=["settings"])
            new_synced_destination.save()
            return destination
        return None

    @staticmethod
    def get_label(destination: DestinationConfig) -> str:
        """
        Returns the e-mail address represented by this destination
        """
        return destination.settings.get("email_address")

    @classmethod
    def has_duplicate(self, queryset: QuerySet, settings: dict) -> bool:
        """
        Returns True if an email destination with the same email address
        already exists in the given queryset
        """
        return queryset.filter(settings__email_address=settings["email_address"]).exists()

    @staticmethod
    def send(event: Event, destinations: QuerySet[DestinationConfig], **_) -> bool:
        """
        Sends email about a given event to the given email destinations

        Returns False if no email destinations were given and
        True if emails were sent
        """
        email_destinations = destinations.filter(media_id=EmailNotification.MEDIA_SLUG)
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
