from django.test import TestCase, override_settings

from argus.incident.ticket.base import TicketPluginException
from argus.util.utils import import_class_from_dotted_path


class RequestTrackerTicketPluginTests(TestCase):
    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"password": "value"},
        TICKET_INFORMATION={"queue": "value"},
    )
    def test_import_settings_raises_error_when_username_is_missing_from_ticket_authentication_secret(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.request_tracker.RequestTrackerPlugin")

        with self.assertRaises(TicketPluginException):
            ticket_class.import_settings()

    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"username": "value"},
        TICKET_INFORMATION={"queue": "value"},
    )
    def test_import_settings_raises_error_when_password_is_missing_from_ticket_authentication_secret(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.request_tracker.RequestTrackerPlugin")

        with self.assertRaises(TicketPluginException):
            ticket_class.import_settings()

    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"username": "value", "password": "value"},
        TICKET_INFORMATION={"key": "value"},
    )
    def test_import_settings_raises_error_when_queue_is_missing_from_ticket_information(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.request_tracker.RequestTrackerPlugin")

        with self.assertRaises(TicketPluginException):
            ticket_class.import_settings()
