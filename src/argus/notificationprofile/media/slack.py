from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from rest_framework.exceptions import ValidationError

from .base import AppriseMedium

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    User = get_user_model()

LOG = logging.getLogger(__name__)

__all__ = [
    "SlackNotification",
]


class SlackNotification(AppriseMedium):
    MEDIA_SLUG = "slack"
    MEDIA_NAME = "Slack"
    MEDIA_JSON_SCHEMA = {
        "title": "Slack Settings",
        "description": "Settings for a DestinationConfig using Slack.",
        "type": "object",
        "required": ["destination_url"],
        "properties": {"destination_url": {"type": "string", "title": "Slack Webhook"}},
    }

    class Form(forms.Form):
        destination_url = forms.CharField()

    @classmethod
    def validate(cls, instance, slack_dict, user):
        cleaned_data = super().validate(instance, slack_dict, user)
        destination_url = cleaned_data["destination_url"]
        if not destination_url.startswith(("https://hooks.slack.com/", "slack://")):
            raise ValidationError(
                {
                    "destination_url": "Not a valid Slack destination URL. Use a Slack incoming webhook (https://hooks.slack.com/...) or an Apprise Slack URL (slack://...)."
                }
            )
        return cleaned_data
