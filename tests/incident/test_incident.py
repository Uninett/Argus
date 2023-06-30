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

    def test_event_has_description(self):
        source_incident_id = "abcknekkebrod"
        incident = Incident.objects.create(
            start_time=timezone.now(),
            end_time=datetime_utils.INFINITY_REPR,
            source_incident_id=source_incident_id,
            source=SourceSystemFactory(),
            description=f"Incident #{source_incident_id} created for testing",
        )
        incident.create_first_event()
        event_start = incident.events.filter(type=Event.Type.INCIDENT_START)

        self.assertTrue(event_start)
        self.assertEqual(incident.description, incident.events.get(type="STA").description)

    def test_new_stateless_incident_has_stateless_event(self):
        source_incident_id = "abcknekkebrod"
        incident = Incident.objects.create(
            start_time=timezone.now(),
            end_time=None,
            source_incident_id=source_incident_id,
            source=SourceSystemFactory(),
            description=f"Incident #{source_incident_id} created for testing",
        )
        incident.create_first_event()
        event_stateless = incident.events.filter(type=Event.Type.STATELESS)

        self.assertEqual(1, event_stateless.count())
