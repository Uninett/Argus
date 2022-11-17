from __future__ import annotations

import gitlab
import logging
from typing import TYPE_CHECKING

from .base import TicketPlugin, TicketPluginException

if TYPE_CHECKING:
    from argus.incident.models import Incident

LOG = logging.getLogger(__name__)

__all__ = [
    "GitlabPlugin",
]


class GitlabPlugin(TicketPlugin):
    @classmethod
    def import_settings(cls):
        try:
            endpoint, authentication, ticket_information = super().import_settings()
        except ValueError as e:
            LOG.exception("Could not import settings for ticket plugin.")
            raise TicketPluginException(f"Gitlab: {e}")

        if "token" not in authentication.keys():
            LOG.error(
                "Gitlab: No token can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )
            raise TicketPluginException(
                "Gitlab: No token can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )

        if "project_namespace_and_name" not in ticket_information.keys():
            LOG.error(
                "Gitlab: No project namespace and name can be found in the ticket information. Please update the setting 'TICKET_INFORMATION'."
            )
            raise TicketPluginException(
                "Gitlab: No project namespace and name can be found in the ticket information. Please update the setting 'TICKET_INFORMATION'."
            )

        return endpoint, authentication, ticket_information

    @staticmethod
    def create_client(endpoint, authentication):
        """Creates and returns a Gitlab client"""
        try:
            client = gitlab.Gitlab(url=endpoint, private_token=authentication["token"])
        except Exception as e:
            LOG.exception("Gitlab: Client could not be created.")
            raise TicketPluginException(f"Gitlab: {e}")
        else:
            return client

    @classmethod
    def create_ticket(cls, incident: Incident):
        """
        Creates a Gitlab ticket with the incident as template and returns the
        ticket url
        """
        endpoint, authentication, ticket_information = cls.import_settings()

        with cls.create_client(endpoint, authentication) as client:
            try:
                project = client.projects.get(ticket_information["project_namespace_and_name"])
                ticket = project.issues.create(
                    {
                        "title": str(incident),
                        "description": incident.description,
                    }
                )
            except Exception as e:
                LOG.exception("Gitlab: Ticket could not be created.")
                raise TicketPluginException(f"Gitlab: {e}")
            else:
                return ticket.web_url
