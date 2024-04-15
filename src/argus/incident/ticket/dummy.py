"""
Minimal ticket creation plugin

Serves as an example and is also used for testing.

Inspired by django.core.mail.outbox, see https://docs.djangoproject.com/en/4.2/topics/testing/tools/#email-services
"""

from __future__ import annotations

from factory import Faker
import logging
from typing import TYPE_CHECKING

from .base import TicketPlugin

if TYPE_CHECKING:
    from argus.incident.models import Incident

LOG = logging.getLogger(__name__)

__all__ = [
    "DummyPlugin",
]

# Do not write to this directly
created_tickets = []  # Filled by TicketTestClient


def _get_fake_url():
    faker = Faker("url")
    return faker.evaluate({}, None, {"locale": Faker._DEFAULT_LOCALE})


def empty_created_tickets():
    "Safely empty out the list of created tickets"

    global created_tickets
    created_tickets = []


class TicketTestClient:
    "Mock ticket client, for testing"

    def __init__(self, endpoint, authentication):
        """Initialize the client that will chat to the ticket system

        All ticket systems we have seen so far seem to use this pattern to
        initialize the client.
        """

        self.authentication = authentication
        self.endpoint = endpoint

    def create(self, *args, **kwargs):
        """Fake writing to an external ticket system

        Use ``empty_created_tickets()`` to reset.
        """
        global created_tickets
        created_tickets.append((*args, kwargs))

        return _get_fake_url()


class DummyPlugin(TicketPlugin):
    """Example of a minimal plugin, can be used for testing"""

    @classmethod
    def import_settings(cls):
        """Import ticket-specific settings from Django settings file

        Return format::

            (absolute endpoint, authentication, plugin-specific additional data)

        This plugin cannot be configured via Django settings, therefore it
        returns dummy values.
        """

        return _get_fake_url(), None, None

    @staticmethod
    def create_client(endpoint, authentication):
        "Instantiate and return ticket system client"
        return TicketTestClient(endpoint, authentication)

    @classmethod
    def create_ticket(cls, serialized_incident: dict):
        """Create a ticket in the ticket system and return the new url

        Since this is a dummy, the actual ticket is stored locally so that the
        method itself can be tested. A dummy url is returned. Observe that the
        returned url need not in any way resemble the url of the endpoint, so
        never assume a specific shape of the url when testing.
        """

        endpoint, authentication, ticket_information = cls.import_settings()

        client = cls.create_client(endpoint=endpoint, authentication=authentication)
        ticket_url = client.create(
            {
                "title": serialized_incident["description"],
                "description": serialized_incident["description"],
            }
        )

        return ticket_url
