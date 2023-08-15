from django.test import TestCase
from django.utils import timezone

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
        event = incident.events.filter(type=Event.Type.STATELESS)

        self.assertEqual(1, event.count())
        self.assertEqual(incident.description, event.description)
