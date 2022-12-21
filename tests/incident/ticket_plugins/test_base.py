from django.conf import settings
from django.test import TestCase, override_settings

from argus.incident.ticket.base import TicketSettingsException
from argus.util.utils import import_class_from_dotted_path


class CreateClientTests(TestCase):
    def test_create_client_returns_client(self):
        plugin = getattr(settings, "TICKET_PLUGIN", None)
        endpoint = getattr(settings, "TICKET_ENDPOINT", None)
        authentication = getattr(settings, "TICKET_AUTHENTICATION_SECRET", None)

        if not plugin or not endpoint or not authentication:
            self.skipTest("No ticket plugin, endpoint or authentication provided.")

        ticket_class = import_class_from_dotted_path(plugin)

        self.assertTrue(ticket_class.create_client(endpoint, authentication))


class ImportSettingsTests(TestCase):
    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"key": "value"},
        TICKET_INFORMATION={"key": "value"},
    )
    def test_import_settings_works_when_all_ticket_settings_are_set(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.base.TicketPlugin")

        endpoint, authentication, ticket_information = ticket_class.import_settings()

        self.assertTrue(endpoint)
        self.assertTrue(authentication)
        self.assertTrue(ticket_information)

    @override_settings(
        TICKET_ENDPOINT=None,
        TICKET_AUTHENTICATION_SECRET={"key": "value"},
        TICKET_INFORMATION={"key": "value"},
    )
    def test_import_settings_raises_error_when_ticket_endpoint_is_missing(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.base.TicketPlugin")

        with self.assertRaises(TicketSettingsException):
            ticket_class.import_settings()

    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={},
        TICKET_INFORMATION={"key": "value"},
    )
    def test_import_settings_raises_error_when_ticket_authentication_secret_is_missing(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.base.TicketPlugin")

        with self.assertRaises(TicketSettingsException):
            ticket_class.import_settings()

    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"key": "value"},
        TICKET_INFORMATION={},
    )
    def test_import_settings_raises_error_when_ticket_information_is_missing(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.base.TicketPlugin")

        with self.assertRaises(TicketSettingsException):
            ticket_class.import_settings()
