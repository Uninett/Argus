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
    "GitlabPlugin",
]

ISSUE_ENDPOINT = getattr(settings, "ISSUE_ENDPOINT")


class GitlabPlugin(IssuePlugin):
    def generate_issue_url(incident: Incident):
        """
        Generate and return an url to a new Gitlab issue with pre-filled
        values from a given incident
        """
        if not ISSUE_ENDPOINT:
            raise ValueError(
                "No endpoint to issue system can be found in the settings. Please update the setting 'ISSUE_ENDPOINT'."
            )
        base_url = urljoin(ISSUE_ENDPOINT, "-/issues/")
        parameter_str = "new?"
        # Title
        if incident.description:
            parameter_str += f"issue[title]={quote(str(incident))}&"
        # Description
        parameter_str += f"issue[description]={quote(incident.description)}"
        return urljoin(base_url, parameter_str)
