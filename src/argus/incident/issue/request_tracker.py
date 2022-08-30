from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin

from django.conf import settings

from .base import IssuePlugin

if TYPE_CHECKING:
    from argus.incident.models import Incident

LOG = logging.getLogger(__name__)

__all__ = [
    "RequestTrackerPlugin",
]

ISSUE_ENDPOINT = getattr(settings, "ISSUE_ENDPOINT")


class RequestTrackerPlugin(IssuePlugin):
    def generate_issue_url(incident: Incident):
        if not ISSUE_ENDPOINT:
            raise ValueError(
                "No endpoint to issue system can be found in the settings. Please update the setting 'ISSUE_ENDPOINT'."
            )

        base_url = urljoin(ISSUE_ENDPOINT, "Ticket/")
        parameter_str = "Create.html?"
        # Title
        if incident.description:
            parameter_str += f"Subject={quote(incident.description)}&"
        # Body
        parameter_str += f"Content={quote(incident.description)}"
        return urljoin(base_url, parameter_str)
