from django.test import TestCase, override_settings

from argus.incident.ticket.base import (
    TicketSettingsException,
    TicketPluginImportException,
)
from argus.incident.ticket.utils import get_autocreate_ticket_plugin, SETTING_NAME


class GetAutocreateTicketPluginTests(TestCase):
    @override_settings(**{SETTING_NAME: None})
    def test_plugin_path_setting_not_set_should_raise_TicketSettingsException(self):
        with self.assertRaises(TicketSettingsException):
            get_autocreate_ticket_plugin()

    @override_settings(**{SETTING_NAME: "nonexistent.path"})
    def test_plugin_path_setting_set_to_bullshit_should_raise_TicketPluginImportException(self):
        with self.assertRaises(TicketPluginImportException):
            get_autocreate_ticket_plugin()
