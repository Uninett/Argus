from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rest_framework.exceptions import ValidationError

from .base import AppriseMedium

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    from ..serializers import RequestDestinationConfigSerializer

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

    @classmethod
    def validate(cls, instance: RequestDestinationConfigSerializer, slack_dict: dict, user: User) -> dict:
        """
        Validates the settings of a slack destination and returns a dict
        with validated and cleaned data
        """
        form = cls.Form(slack_dict["settings"])
        if not form.is_valid():
            raise ValidationError(form.errors)
        if user.destinations.filter(
            media_id="slack", settings__destination_url=form.cleaned_data["destination_url"]
        ).exists():
            raise ValidationError({"destination_url": "Webhook already exists"})

        return form.cleaned_data
