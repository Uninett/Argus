from __future__ import annotations

from abc import ABC, abstractmethod

from django.conf import settings

__all__ = [
    "TicketPlugin",
    "TicketPluginException",
]


class TicketPluginException(Exception):
    """Ticket plugin exception"""


class TicketPlugin(ABC):
    @classmethod
    def import_settings(cls):
        """
        Imports, validates and returns settings needed for ticket creation.
        Raises a ValueError if settings are not set properly
        """
        endpoint = getattr(settings, "TICKET_ENDPOINT")
        if not endpoint:
            raise ValueError("No endpoint can be found in the settings. Please update the setting 'TICKET_ENDPOINT'.")

        authentication = getattr(settings, "TICKET_AUTHENTICATION_SECRET")
        if not authentication:
            raise ValueError(
                "No authentication information can be found in the settings. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )

        ticket_information = getattr(settings, "TICKET_INFORMATION")
        if not ticket_information:
            raise ValueError(
                "No extra information for ticket creation can be found in the settings. Please update the setting 'TICKET_INFORMATION'."
            )

        return endpoint, authentication, ticket_information

    @staticmethod
    @abstractmethod
    def create_client(endpoint, authentication):
        """
        Creates, authenticates and returns a client to connect with the given
        endpoint

        Raises a TicketPluginException in case of any errors
        """
        return None

    @classmethod
    @abstractmethod
    def create_ticket(cls, incident):
        """
        Creates a ticket with the information of the given incident and returns
        its url

        Raises a TicketPluginException in case of any errors
        """
        return None
