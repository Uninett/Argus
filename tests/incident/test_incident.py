from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from argus.incident.factories import (
    AcknowledgementFactory,
    EventFactory,
    StatefulIncidentFactory,
    StatelessIncidentFactory,
)
from argus.incident.models import Event
from argus.incident.factories import SourceSystemFactory, SourceUserFactory
from argus.util.testing import disconnect_signals, connect_signals


class CreateIncidentTests(TestCase):
    def setUp(self):
        disconnect_signals()
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(user=source_user)

    def tearDown(self):
        connect_signals()

    def test_new_stateful_incident_has_single_start_event(self):
        incident = StatefulIncidentFactory(source=self.source)
        incident.create_first_event()
        events = incident.events.filter(type=Event.Type.INCIDENT_START)

        self.assertEqual(events.count(), 1)
        self.assertEqual(events.get().description, incident.description)

    def test_new_stateless_incident_has_single_stateless_event(self):
        incident = StatelessIncidentFactory(source=self.source)
        incident.create_first_event()
        events = incident.events.filter(type=Event.Type.STATELESS)

        self.assertEqual(events.count(), 1)
        self.assertEqual(events.get().description, incident.description)


class IncidentAckedTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_acked_is_true_for_incident_with_acknowledgement_without_expiration(self):
        ack = AcknowledgementFactory()
        self.assertTrue(ack.event.incident.acked)

    def test_acked_is_true_for_incident_with_acknowledgement_with_future_expiration(self):
        ack = AcknowledgementFactory(expiration=timezone.now() + timedelta(days=3))
        self.assertTrue(ack.event.incident.acked)

    def test_acked_is_true_for_incident_with_ack_event_but_no_acknowledgement(self):
        """
        This is specifically for when acknowledgements are created.

        Since we first create the event and then the acknowledgement the
        notification sending is triggered already on the event creation,
        which is why this test is necessary
        """
        event = EventFactory(type=Event.Type.ACKNOWLEDGE)
        self.assertTrue(event.incident.acked)

    def test_acked_is_false_for_incident_with_acknowledgement_with_past_expiration(self):
        timestamp = timezone.now() - timedelta(days=1)
        event = EventFactory(timestamp=timestamp, type=Event.Type.ACKNOWLEDGE)
        ack = AcknowledgementFactory(event=event, expiration=timestamp)
        self.assertFalse(ack.event.incident.acked)

    def test_acked_is_false_for_incident_without_acknowledgement(self):
        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        incident = StatefulIncidentFactory(source=source)
        self.assertFalse(incident.acked)


class IncidentLevelTests(TestCase):
    def setup(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_level_str_returns_name_of_level(self):
        incident = StatefulIncidentFactory(level=1)
        self.assertEqual(incident.pp_level(), "Critical")
