from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone

from argus.filter.factories import FilterFactory
from argus.incident.factories import StatefulIncidentFactory
from argus.incident.models import Incident
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.plannedmaintenance.utils import incidents_covered_by_planned_maintenance_task
from argus.util.testing import disconnect_signals, connect_signals


@tag("database")
class TestIncidentsCoveredByPlannedMaintenanceTask(TestCase):
    def setUp(self):
        disconnect_signals()
        self.open_incident = StatefulIncidentFactory(level=5)
        self.maxlevel_filter = FilterFactory(filter={"maxlevel": 5})

    def teardown(self):
        connect_signals()

    def test_returns_only_open_incidents(self):
        closed_incident = StatefulIncidentFactory(end_time=timezone.now())
        pm = PlannedMaintenanceFactory()
        pm.filters.add(self.maxlevel_filter)
        incidents = incidents_covered_by_planned_maintenance_task(queryset=Incident.objects.all(), pm_task=pm)

        self.assertIn(self.open_incident, incidents)
        self.assertNotIn(closed_incident, incidents)

    def test_given_past_pm_returns_no_incidents(self):
        pm = PlannedMaintenanceFactory(
            start_time=timezone.now() - timedelta(days=2), end_time=timezone.now() - timedelta(days=1)
        )
        pm.filters.add(self.maxlevel_filter)

        incidents = incidents_covered_by_planned_maintenance_task(queryset=Incident.objects.all(), pm_task=pm)
        self.assertFalse(incidents)

    def test_given_future_pm_returns_no_incidents(self):
        pm = PlannedMaintenanceFactory(start_time=timezone.now() + timedelta(days=2))
        pm.filters.add(self.maxlevel_filter)

        incidents = incidents_covered_by_planned_maintenance_task(queryset=Incident.objects.all(), pm_task=pm)
        self.assertFalse(incidents)

    def test_given_filter_only_returns_incidents_matching_filter(self):
        important_incident = StatefulIncidentFactory(level=1)
        pm = PlannedMaintenanceFactory()
        pm.filters.add(FilterFactory(filter={"maxlevel": 1}))

        incidents = incidents_covered_by_planned_maintenance_task(queryset=Incident.objects.all(), pm_task=pm)

        self.assertIn(important_incident, incidents)
        self.assertNotIn(self.open_incident, incidents)
