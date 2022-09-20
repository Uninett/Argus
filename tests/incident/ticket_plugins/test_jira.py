from django.test import TestCase, override_settings

from argus.incident.ticket.base import TicketPluginException
from argus.util.utils import import_class_from_dotted_path


class JiraTicketPluginTests(TestCase):
    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"key": "value"},
        TICKET_INFORMATION={"project_key_or_id": "value"},
    )
    def test_import_settings_raises_error_if_token_is_missing_from_ticket_authentication_secret(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.jira.JiraPlugin")

        with self.assertRaises(TicketPluginException):
            ticket_class.import_settings()

    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"token": "value"},
        TICKET_INFORMATION={"key": "value"},
    )
    def test_import_settings_raises_error_if_project_key_or_id_is_missing_from_ticket_information(self):
        ticket_class = import_class_from_dotted_path("argus.incident.ticket.jira.JiraPlugin")

        with self.assertRaises(TicketPluginException):
            ticket_class.import_settings()
