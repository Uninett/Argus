from unittest import TestCase
from unittest.mock import patch
from datetime import timedelta

from django.test import TestCase as DjangoTestCase, override_settings, tag

from argus.htmx.templatetags.argus_htmx import dictvalue, pretty_timedelta, ticket_identifier
from argus.incident.factories import StatefulIncidentFactory
from argus.incident.ticket.dummy import DummyPlugin
from argus.incident.ticket.utils import SETTING_NAME
from argus.util.testing import connect_signals, disconnect_signals


@tag("unit")
class DictvalueTests(TestCase):
    def test_get_value_from_dict_golden_path(self):
        testdict = {1: 1, 2: 2}
        self.assertEqual(dictvalue(testdict, 1), 1)

    def test_get_value_from_dict_when_key_is_missing_returns_None(self):
        testdict = {}
        self.assertIsNone(dictvalue(testdict, 1))

    def test_get_value_from_dict_when_key_is_missing_and_default_is_set_returns_default(self):
        testdict = {}
        self.assertEqual(dictvalue(testdict, 1, "boo"), "boo")


@tag("unit")
class PrettyTimedeltaTest(TestCase):
    def test_pretty_timedelta_when_value_is_None_return_fallback(self):
        result = pretty_timedelta(None, "foo")
        self.assertEqual(result, "foo")

    def test_when_value_is_zero_return_constant_string(self):
        result = pretty_timedelta(timedelta(seconds=0))
        self.assertEqual(result, "0\xa0minutes")

    def test_when_value_is_positive_return_calculated_string(self):
        result = pretty_timedelta(timedelta(seconds=1))
        self.assertEqual(result, "0\xa0minutes")
        result = pretty_timedelta(timedelta(seconds=10))
        self.assertEqual(result, "0\xa0minutes")
        result = pretty_timedelta(timedelta(seconds=100000))
        self.assertEqual(result, "1\xa0day, 3\xa0hours")

    def test_when_value_is_negative_return_0_minutes(self):
        result = pretty_timedelta(timedelta(seconds=-1))
        self.assertEqual(result, "0\xa0minutes")
        result = pretty_timedelta(timedelta(seconds=-10))
        self.assertEqual(result, "0\xa0minutes")
        result = pretty_timedelta(timedelta(seconds=-100000))
        self.assertEqual(result, "0\xa0minutes")


@tag("unit")
class TicketIdentifierTests(DjangoTestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_when_incident_has_no_ticket_url_returns_empty_string(self):
        incident = StatefulIncidentFactory(ticket_url="")
        self.assertEqual(ticket_identifier(incident), "")

    @override_settings(**{SETTING_NAME: None})
    def test_when_no_ticket_plugin_is_configured_falls_back_to_ticket_url(self):
        incident = StatefulIncidentFactory(ticket_url="https://example.com/ticket/123")
        self.assertEqual(ticket_identifier(incident), incident.ticket_url)

    @override_settings(**{SETTING_NAME: "argus.incident.ticket.dummy.DummyPlugin"})
    def test_when_ticket_plugin_is_configured_uses_its_get_ticket_identifier(self):
        incident = StatefulIncidentFactory(ticket_url="https://example.com/ticket/123")
        with patch.object(DummyPlugin, "get_ticket_identifier", return_value="TICKET-1"):
            self.assertEqual(ticket_identifier(incident), "TICKET-1")
