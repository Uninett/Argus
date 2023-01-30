from __future__ import annotations

from abc import ABC, abstractmethod

from django.conf import settings
from django.template.loader import render_to_string

__all__ = [
    "TicketClientException",
    "TicketCreationException",
    "TicketPlugin",
    "TicketPluginException",
    "TicketSettingsException",
]


class TicketPluginException(Exception):
    """Ticket plugin exception"""


class TicketSettingsException(TicketPluginException):
    """Some of the settings required for the ticket plugins are not set
    properly
    """


class TicketClientException(TicketPluginException):
    """There was an error creating the client for interaction with the ticket
    system
    """


class TicketCreationException(TicketPluginException):
    """There was an error creating a ticket in the ticket system"""


class TicketPlugin(ABC):
    @classmethod
    def import_settings(cls):
        """
        Imports, validates and returns settings needed for ticket creation.

        Raises a TicketSettingsException if settings are not set
        properly.
        """
        endpoint = getattr(settings, "TICKET_ENDPOINT", None)
        if not endpoint:
            raise TicketSettingsException(
                "No endpoint can be found in the settings. Please check and update the     setting 'TICKET_ENDPOINT'."
            )

        authentication = getattr(settings, "TICKET_AUTHENTICATION_SECRET", None)
        if not authentication:
            raise TicketSettingsException(
                "No correct authentication information can be found in the settings. Please check and update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )

        ticket_information = getattr(settings, "TICKET_INFORMATION", None)
        if not ticket_information:
            raise TicketSettingsException(
                "No correct extra information for ticket creation can be found in the settings. Please check and update the setting 'TICKET_INFORMATION'."
            )

        return endpoint, authentication, ticket_information

    @staticmethod
    @abstractmethod
    def create_client(endpoint, authentication):
        """
        Creates, authenticates and returns a client to connect with the given
        endpoint

        Raises a TicketClientException in case of any errors
        """
        return None

    @staticmethod
    def create_html_body(serialized_incident: dict) -> str:
        return render_to_string("incident/ticket/default_ticket_body.html", serialized_incident)

    @classmethod
    @abstractmethod
    def create_ticket(cls, serialized_incident: dict):
        """
        Creates a ticket with the information of the given incident and returns
        its url

        Raises a TicketCreationException in case of any errors
        """
        return None
