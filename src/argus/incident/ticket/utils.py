from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from django.conf import settings

from argus.incident.ticket.base import (
    TicketSettingsException,
)
from argus.util.utils import import_class_from_dotted_path

from ..serializers import IncidentSerializer

if TYPE_CHECKING:
    from argus.incident.models import Incident
    from django.contrib.auth import get_user_model

    User = get_user_model()


LOG = logging.getLogger(__name__)
SETTING_NAME = "TICKET_PLUGIN"


__all__ = [
    "SETTING_NAME",
    "get_autocreate_ticket_plugin",
    "serialize_incident_for_ticket_autocreation",
]


def get_autocreate_ticket_plugin():
    plugin = getattr(settings, SETTING_NAME, None)

    if not plugin:
        raise TicketSettingsException(
            f'No path to ticket plugin can be found in the settings. Please update the setting "{SETTING_NAME}".'
        )

    try:
        ticket_class = import_class_from_dotted_path(plugin)
    except Exception as e:
        LOG.exception("Could not import ticket plugin from path %s", plugin)
        raise TicketSettingsException(f"Ticket plugin is incorrectly configured: {e}")
    else:
        return ticket_class


def serialize_incident_for_ticket_autocreation(incident: Incident, actor: User):
    serialized_incident = IncidentSerializer(incident).data
    # TODO: ensure argus_url ends with "/" on HTMx frontend
    serialized_incident["argus_url"] = urljoin(
        getattr(settings, "FRONTEND_URL", ""),
        f"incidents/{incident.pk}",
    )
    serialized_incident["user"] = actor.get_full_name()
    return serialized_incident
