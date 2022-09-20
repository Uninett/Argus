from __future__ import annotations

from jira import JIRA
import logging
from typing import TYPE_CHECKING

from .base import TicketPlugin, TicketPluginException

if TYPE_CHECKING:
    from argus.incident.models import Incident

LOG = logging.getLogger(__name__)

__all__ = [
    "JiraPlugin",
]


class JiraPlugin(TicketPlugin):
    @classmethod
    def import_settings(cls):
        try:
            endpoint, authentication, ticket_information = super().import_settings()
        except ValueError as e:
            LOG.exception("Could not import settings for ticket plugin.")
            raise TicketPluginException(f"Jira: {e}")

        if "token" not in authentication.keys():
            LOG.error(
                "Jira: No token can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )
            raise TicketPluginException(
                "Jira: No token can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )

        if "project_key_or_id" not in ticket_information.keys():
            LOG.error(
                "Jira: No project key or id can be found in the ticket information. Please update the setting 'TICKET_INFORMATION'."
            )
            raise TicketPluginException(
                "Jira: No project key or id can be found in the ticket information. Please update the setting 'TICKET_INFORMATION'."
            )

        return endpoint, authentication, ticket_information

    @staticmethod
    def create_client(endpoint, authentication):
        """Creates and returns a Jira client"""
        # different between self hosted and cloud hosted
        # cloud: need email & api token
        # self: only api token

        try:
            if "email" in authentication.keys():
                client = JIRA(
                    server=endpoint,
                    basic_auth=(authentication["email"], authentication["token"]),
                )

            client = JIRA(
                server=endpoint,
                token_auth=authentication["token"],
            )
        except Exception as e:
            LOG.exception("Jira: Client could not be created.")
            raise TicketPluginException(f"Jira: {e}")
        else:
            return client

    @classmethod
    def create_ticket(cls, incident: Incident):
        """
        Creates a Jira ticket with the incident as template and returns the
        ticket url
        """
        endpoint, authentication, ticket_information = cls.import_settings()

        ticket_type = ticket_information["type"] if "type" in ticket_information.keys() else "Task"

        client = cls.create_client(endpoint, authentication)

        try:
            ticket = client.create_issue(
                project=ticket_information["project_key_or_id"],
                summary=str(incident),
                description=incident.description,
                issuetype=ticket_type,
            )
        except Exception as e:
            LOG.exception("Jira: Ticket could not be created.")
            raise TicketPluginException(f"Jira: {e}")
        else:
            return ticket.permalink()
