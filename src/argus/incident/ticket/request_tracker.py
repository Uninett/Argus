from __future__ import annotations

import logging
from rt_client.client import Client
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from .base import TicketPlugin, TicketPluginException

if TYPE_CHECKING:
    from argus.incident.models import Incident

LOG = logging.getLogger(__name__)

__all__ = [
    "RequestTrackerPlugin",
]


class RequestTrackerPlugin(TicketPlugin):
    @classmethod
    def import_settings(cls):
        try:
            endpoint, authentication, ticket_information = super().import_settings()
        except ValueError as e:
            LOG.exception("Could not import settings for ticket plugin.")
            raise TicketPluginException(f"Request Tracker: {e}")

        if "username" not in authentication.keys() or "password" not in authentication.keys():
            LOG.error(
                "Request Tracker: No username or password can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )
            raise TicketPluginException(
                "Request Tracker: No username or password can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )

        if "queue" not in ticket_information.keys():
            LOG.error(
                "Request Tracker: No queue can be found in the ticket information. Please update the setting 'TICKET_INFORMATION'."
            )
            raise TicketPluginException(
                "Request Tracker: No queue can be found in the ticket information. Please update the setting 'TICKET_INFORMATION'."
            )

        return endpoint, authentication, ticket_information

    @staticmethod
    def create_client(endpoint, authentication):
        """Creates and returns a RT client"""
        try:
            client = Client(
                username=authentication["username"],
                password=authentication["password"],
                endpoint=endpoint,
            )
        except Exception as e:
            LOG.exception("Request Tracker: Client could not be created.")
            raise TicketPluginException(f"Request Tracker: {e}")
        else:
            return client

    @classmethod
    def create_ticket(cls, incident: Incident):
        """
        Creates a Request Tracker ticket with the incident as template and returns the
        ticket url
        """
        endpoint, authentication, ticket_information = cls.import_settings()

        client = cls.create_client(endpoint, authentication)
        data = {
            "Queue": ticket_information["queue"],
            "Subject": str(incident),
            "Text": incident.description,
        }

        try:
            ticket_id = client.ticket.create(attrs=data)["id"]
        except Exception as e:
            LOG.exception("Request Tracker: Ticket could not be created.")
            raise TicketPluginException(f"Request Tracker: {e}")
        else:
            ticket_url = urljoin(endpoint, f"Ticket/Display.html?id={ticket_id}")
            return ticket_url
