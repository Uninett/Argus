from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.incident.factories import (
    SourceSystemFactory,
    SourceUserFactory,
    StatefulIncidentFactory,
)
from argus.incident.models import Incident
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
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


class UnderMaintenanceQuerySetTests(TestCase):
    def setUp(self):
        disconnect_signals()
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(user=source_user)
        self.now = timezone.now()

    def tearDown(self):
        connect_signals()

    def test_when_incident_has_active_maintenance_task_then_it_should_be_included(self):
        incident = StatefulIncidentFactory(source=self.source)
        pm_task = PlannedMaintenanceFactory(
            start_time=self.now - timedelta(hours=1),
            end_time=self.now + timedelta(hours=1),
        )
        pm_task.incidents.add(incident)
        result = Incident.objects.under_maintenance()
        self.assertIn(incident, result)

    def test_when_incident_has_no_maintenance_task_then_it_should_be_excluded(self):
        incident = StatefulIncidentFactory(source=self.source)
        result = Incident.objects.under_maintenance()
        self.assertNotIn(incident, result)

    def test_when_incident_has_only_past_maintenance_task_then_it_should_be_excluded(self):
        incident = StatefulIncidentFactory(source=self.source)
        pm_task = PlannedMaintenanceFactory(
            start_time=self.now - timedelta(hours=2),
            end_time=self.now - timedelta(hours=1),
        )
        pm_task.incidents.add(incident)
        result = Incident.objects.under_maintenance()
        self.assertNotIn(incident, result)
