from io import StringIO
import contextlib

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from argus.incident.factories import (
    SourceSystemFactory,
    SourceSystemTypeFactory,
    SourceUserFactory,
    StatefulIncidentFactory,
)
from argus.incident.management.commands.find_unset_last_seen import find_latest_event_by_heartbeatless_source
from argus.incident.models import Event
from argus.util.testing import connect_signals, disconnect_signals


class FindLatestEventByHeartbeatlessSourceTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_given_no_unset_last_seen_sources_then_return_empty_lists(self):
        name = "setlastseen"
        user = SourceUserFactory(username=name)
        sst = SourceSystemTypeFactory(name=name)
        SourceSystemFactory(user=user, name=name, type=sst, last_seen=timezone.now())

        changes, never_seen = find_latest_event_by_heartbeatless_source()
        self.assertEqual(changes, [])
        self.assertEqual(never_seen, [])

    def test_given_unset_last_seen_source_with_connected_event_then_return_source_in_changes(self):
        name = "nolastseen"
        user = SourceUserFactory(username=name)
        sst = SourceSystemTypeFactory(name=name)
        source = SourceSystemFactory(user=user, name=name, type=sst)
        incident = StatefulIncidentFactory(source=source)
        now = timezone.now()
        Event.objects.create(
            incident=incident,
            actor=source.user,
            timestamp=now,
            received=now,
            type=Event.Type.INCIDENT_START,
            description="",
        )

        changes, never_seen = find_latest_event_by_heartbeatless_source()
        self.assertIn((source, now), changes)
        self.assertEqual(never_seen, [])

    def test_given_unset_last_seen_source_without_connected_events_then_return_source_as_never_seen(self):
        name = "nolastseen"
        user = SourceUserFactory(username=name)
        sst = SourceSystemTypeFactory(name=name)
        source = SourceSystemFactory(user=user, name=name, type=sst)

        changes, never_seen = find_latest_event_by_heartbeatless_source()
        self.assertEqual(changes, [])
        self.assertIn(source, never_seen)


class FindUnsetLastSeenTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.name = "nolastseen"
        self.user = SourceUserFactory(username=self.name)
        self.sst = SourceSystemTypeFactory(name=self.name)
        self.source = SourceSystemFactory(user=self.user, name=self.name, type=self.sst)

    def tearDown(self):
        connect_signals()

    def test_given_unset_last_seen_source_with_connected_event_then_print_source_as_possibly_dead(self):
        now = timezone.now()
        incident = StatefulIncidentFactory(source=self.source)
        Event.objects.create(
            incident=incident,
            actor=self.source.user,
            timestamp=now,
            received=now,
            type=Event.Type.INCIDENT_START,
            description="",
        )
        F = StringIO()

        with contextlib.redirect_stdout(F):
            call_command("find_unset_last_seen", verbosity=2)

        output = F.getvalue().strip()
        self.assertIn(f"Possibly dead sources:\n{self.source}: {now}", output)

    def test_given_unset_last_seen_source_without_connected_events_then_print_source_as_never_seen(self):
        F = StringIO()

        with contextlib.redirect_stdout(F):
            call_command("find_unset_last_seen", verbosity=2)

        output = F.getvalue().strip()
        self.assertIn(f"Never seen, never put into production?\n{self.name}", output)

    def test_given_unset_last_seen_source_with_connected_event_then_save_last_seen_to_event_received_timestamp(self):
        now = timezone.now()
        incident = StatefulIncidentFactory(source=self.source)
        Event.objects.create(
            incident=incident,
            actor=self.source.user,
            timestamp=now,
            received=now,
            type=Event.Type.INCIDENT_START,
            description="",
        )
        call_command("find_unset_last_seen", "--save", verbosity=0)

        self.source.refresh_from_db()
        self.assertEqual(self.source.last_seen, now)
