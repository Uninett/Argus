from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from argus.incident.factories import AcknowledgementFactory, EventFactory, StatefulIncidentFactory
from argus.incident.models import Incident, Event
from argus.incident.factories import SourceSystemFactory
from argus.util import datetime_utils
from argus.util.testing import disconnect_signals, connect_signals


class CreateIncidentTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_new_stateful_incident_has_single_start_event(self):
        source_incident_id = "abcknekkebrod"
        incident = Incident.objects.create(
            start_time=timezone.now(),
            end_time=datetime_utils.INFINITY_REPR,
            source_incident_id=source_incident_id,
            source=SourceSystemFactory(),
            description=f"Incident #{source_incident_id} created for testing",
        )
        incident.create_first_event()
        events = incident.events.filter(type=Event.Type.INCIDENT_START)

        self.assertEqual(events.count(), 1)
        self.assertEqual(events.get().description, incident.description)

    def test_new_stateless_incident_has_single_stateless_event(self):
        source_incident_id = "abcknekkebrod"
        incident = Incident.objects.create(
            start_time=timezone.now(),
            end_time=None,
            source_incident_id=source_incident_id,
            source=SourceSystemFactory(),
            description=f"Incident #{source_incident_id} created for testing",
        )
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
        incident = StatefulIncidentFactory()
        self.assertFalse(incident.acked)
