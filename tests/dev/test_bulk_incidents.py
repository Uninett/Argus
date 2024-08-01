from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, tag
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.incident.factories import SourceSystemFactory, SourceUserFactory, StatefulIncidentFactory
from argus.incident.models import Event
from argus.util.testing import connect_signals, disconnect_signals


@tag("queryset-filter")
class BulkIncidentsTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.username = "username"
        self.user = PersonUserFactory(username=self.username)
        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        self.incident = StatefulIncidentFactory(start_time=timezone.now() - timedelta(days=1), source=source)
        self.open_filter = FilterFactory(filter={"open": True})
        self.closed_filter = FilterFactory(filter={"open": False})

    def tearDown(self):
        connect_signals()

    def test_bulk_incidents_will_bulk_set_ticket_url_for_filtered_incidents(self):
        ticket_url = "www.example.com/ticket/123"
        call_command(
            "bulk_incidents",
            self.open_filter.pk,
            self.username,
            "ticket_url",
            url=ticket_url,
            stdout=None,
            stderr=None,
        )

        self.incident.refresh_from_db()

        self.assertEqual(self.incident.ticket_url, ticket_url)

    def test_bulk_incidents_will_bulk_ack_filtered_incidents(self):
        call_command(
            "bulk_incidents",
            self.open_filter.pk,
            self.username,
            "ack",
            stdout=None,
            stderr=None,
        )

        self.assertTrue(self.incident.acked)

    def test_bulk_incidents_will_bulk_ack_filtered_incidents_with_set_expiration(self):
        expiration = str(self.incident.start_time + timedelta(days=3))
        call_command(
            "bulk_incidents",
            self.open_filter.pk,
            self.username,
            "ack",
            expiration=expiration,
            stdout=None,
            stderr=None,
        )

        self.assertTrue(self.incident.acked)
        self.assertEqual(str(self.incident.acks.first().expiration), expiration)

    def test_bulk_incidents_will_not_bulk_ack_incidents_for_non_fitting_filter(self):
        call_command(
            "bulk_incidents",
            self.closed_filter.pk,
            self.username,
            "ack",
            stdout=None,
            stderr=None,
        )

        self.assertFalse(self.incident.acked)

    def test_bulk_incidents_will_bulk_close_filtered_incidents(self):
        call_command(
            "bulk_incidents",
            self.open_filter.pk,
            self.username,
            "close",
            stdout=None,
            stderr=None,
        )

        self.incident.refresh_from_db()

        self.assertFalse(self.incident.open)

    def test_bulk_incidents_will_bulk_close_filtered_incidents_with_set_description(self):
        description = "closing"
        call_command(
            "bulk_incidents",
            self.open_filter.pk,
            self.username,
            "close",
            description=description,
            stdout=None,
            stderr=None,
        )

        self.incident.refresh_from_db()

        self.assertFalse(self.incident.open)
        self.assertEqual(self.incident.events.get(type=Event.Type.CLOSE).description, description)

    def test_bulk_incidents_will_bulk_close_filtered_incidents_with_set_timestamp(self):
        timestamp = str(self.incident.start_time - timedelta(hours=1))
        call_command(
            "bulk_incidents",
            self.open_filter.pk,
            self.username,
            "close",
            timestamp=timestamp,
            stdout=None,
            stderr=None,
        )

        self.incident.refresh_from_db()

        self.assertFalse(self.incident.open)
        self.assertEqual(str(self.incident.events.get(type=Event.Type.CLOSE).timestamp), timestamp)

    def test_bulk_incidents_will_bulk_reopen_filtered_incidents(self):
        self.incident.set_closed(actor=self.user)

        call_command(
            "bulk_incidents",
            self.closed_filter.pk,
            self.username,
            "reopen",
            stdout=None,
            stderr=None,
        )

        self.incident.refresh_from_db()

        self.assertTrue(self.incident.open)

    def test_bulk_incidents_will_fail_with_incorrect_username(self):
        err = StringIO()

        call_command(
            "bulk_incidents",
            self.open_filter.pk,
            "wrong_username",
            "ack",
            stdout=None,
            stderr=err,
        )

        self.assertEqual(err.getvalue(), "No user with the given username could be found.\n")
