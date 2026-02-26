from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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
