from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from argus.auth.factories import PersonUserFactory, SourceUserFactory
from argus.incident.factories import (
    SourceSystemFactory,
    SourceSystemTypeFactory,
    StatefulIncidentFactory,
)
from argus.incident.models import Incident
from argus.incident.views import IncidentFilter
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.util.testing import disconnect_signals, connect_signals


class IncidentFilterHideClosedAckedTests(TestCase):
    def setUp(self):
        disconnect_signals()
        source_type = SourceSystemTypeFactory(name="nav")
        source_user = SourceUserFactory(username="nav1")
        self.source = SourceSystemFactory(name="NAV 1", type=source_type, user=source_user)
        self.user = PersonUserFactory()
        self.now = timezone.now()

    def tearDown(self):
        connect_signals()

    def test_when_hide_closed_acked_is_true_then_it_should_exclude_closed_and_acked(self):
        closed_acked = StatefulIncidentFactory(source=self.source, end_time=self.now)
        closed_acked.create_ack(self.user)
        open_incident = StatefulIncidentFactory(source=self.source)

        qs = Incident.objects.order_by("pk")
        result = IncidentFilter.incident_filter(qs, "hide_closed_acked", True)
        self.assertNotIn(closed_acked, result)
        self.assertIn(open_incident, result)

    def test_when_hide_closed_acked_is_false_then_it_should_return_full_queryset(self):
        closed_acked = StatefulIncidentFactory(source=self.source, end_time=self.now)
        closed_acked.create_ack(self.user)

        qs = Incident.objects.order_by("pk")
        result = IncidentFilter.incident_filter(qs, "hide_closed_acked", False)
        self.assertIn(closed_acked, result)


class IncidentFilterUnderMaintenanceTests(TestCase):
    def setUp(self):
        disconnect_signals()
        source_type = SourceSystemTypeFactory(name="nav")
        source_user = SourceUserFactory(username="nav1")
        self.source = SourceSystemFactory(name="NAV 1", type=source_type, user=source_user)
        self.now = timezone.now()

    def tearDown(self):
        connect_signals()

    def test_when_under_maintenance_is_true_then_it_should_return_only_maintained_incidents(self):
        maintained = StatefulIncidentFactory(source=self.source)
        not_maintained = StatefulIncidentFactory(source=self.source)
        pm_task = PlannedMaintenanceFactory(
            start_time=self.now - timedelta(hours=1),
            end_time=self.now + timedelta(hours=1),
        )
        pm_task.incidents.add(maintained)

        qs = Incident.objects.order_by("pk")
        result = IncidentFilter.incident_filter(qs, "under_maintenance", True)
        self.assertIn(maintained, result)
        self.assertNotIn(not_maintained, result)

    def test_when_under_maintenance_is_false_then_it_should_return_full_queryset(self):
        incident = StatefulIncidentFactory(source=self.source)

        qs = Incident.objects.order_by("pk")
        result = IncidentFilter.incident_filter(qs, "under_maintenance", False)
        self.assertIn(incident, result)
