from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from django.conf import settings
from django.utils.timezone import now as tznow

from argus.incident.ticket.base import (
    TicketPluginImportException,
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
    "get_ticket_plugin_path",
    "get_autocreate_ticket_plugin",
    "serialize_incident_for_ticket_autocreation",
    "autocreate_ticket",
]


def get_ticket_plugin_path():
    return getattr(settings, SETTING_NAME, None)


def get_autocreate_ticket_plugin(plugin_path_fetcher=get_ticket_plugin_path):
    plugin_path = plugin_path_fetcher()

    if not plugin_path:
        raise TicketSettingsException(
            f'No path to ticket plugin can be found in the settings. Please update the setting "{SETTING_NAME}".'
        )

    try:
        ticket_class = import_class_from_dotted_path(plugin_path)
    except ModuleNotFoundError:
        error_msg = "Could not import ticket plugin from path %s"
        LOG.exception(error_msg, plugin_path)
        raise TicketPluginImportException(error_msg % plugin_path)
    except Exception:
        error_msg = "Could not import ticket plugin from path %s for unexpected reason"
        LOG.exception(error_msg, plugin_path)
        raise TicketPluginImportException(error_msg % plugin_path)
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


def autocreate_ticket(incident: Incident, user: User, plugin=None, timestamp=None):
    # never overwrite existing url
    if incident.ticket_url:
        return None

    if not plugin:
        plugin = get_autocreate_ticket_plugin()
    if not timestamp:
        timestamp = tznow()

    serialized_incident = serialize_incident_for_ticket_autocreation(incident, user)

    url = plugin.create_ticket(serialized_incident)

    incident.change_ticket_url(user, url, timestamp)

    return incident.ticket_url
