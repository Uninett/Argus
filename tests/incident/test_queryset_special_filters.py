from django.test import TestCase
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.incident.factories import (
    SourceSystemFactory,
    SourceUserFactory,
    StatefulIncidentFactory,
)
from argus.incident.models import Incident
from argus.util.testing import disconnect_signals, connect_signals


class OpenOrUnackedQuerySetTests(TestCase):
    def setUp(self):
        disconnect_signals()
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(user=source_user)
        self.user = PersonUserFactory()
        self.timestamp = timezone.now()

    def tearDown(self):
        connect_signals()

    def test_when_incident_is_open_and_acked_then_it_should_be_included(self):
        incident = StatefulIncidentFactory(source=self.source)
        incident.create_ack(self.user)
        result = Incident.objects.open_or_unacked()
        self.assertIn(incident, result)

    def test_when_incident_is_open_and_unacked_then_it_should_be_included(self):
        incident = StatefulIncidentFactory(source=self.source)
        result = Incident.objects.open_or_unacked()
        self.assertIn(incident, result)

    def test_when_incident_is_closed_and_unacked_then_it_should_be_included(self):
        incident = StatefulIncidentFactory(
            source=self.source,
            end_time=self.timestamp,
        )
        result = Incident.objects.open_or_unacked()
        self.assertIn(incident, result)

    def test_when_incident_is_closed_and_acked_then_it_should_be_excluded(self):
        incident = StatefulIncidentFactory(
            source=self.source,
            end_time=self.timestamp,
        )
        incident.create_ack(self.user)
        result = Incident.objects.open_or_unacked()
        self.assertNotIn(incident, result)
