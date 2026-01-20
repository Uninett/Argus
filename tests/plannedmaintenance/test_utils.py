from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone

from argus.filter.factories import FilterFactory
from argus.incident.factories import EventFactory, StatefulIncidentFactory
from argus.incident.models import Event, Incident
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.plannedmaintenance.models import PlannedMaintenanceTask
from argus.plannedmaintenance.utils import (
    connect_incident_with_planned_maintenance_tasks,
    event_covered_by_planned_maintenance,
    incidents_covered_by_planned_maintenance_task,
)
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


@tag("database")
class TestEventCoveredByPlannedMaintenanceTasks(TestCase):
    def setUp(self):
        disconnect_signals()
        self.default_level = 5
        self.incident = StatefulIncidentFactory(level=self.default_level)
        self.start_event = EventFactory(incident=self.incident, type=Event.Type.INCIDENT_START)
        self.current_pm = PlannedMaintenanceFactory()
        self.maxlevel_filter = FilterFactory(filter={"maxlevel": self.default_level})

    def teardown(self):
        connect_signals()

    def test_given_relevant_event_return_true(self):
        self.current_pm.filters.add(self.maxlevel_filter)

        covered = event_covered_by_planned_maintenance(self.start_event)

        self.assertTrue(covered)

    def test_given_wrong_event_type_return_false(self):
        self.current_pm.filters.add(FilterFactory(filter={"event_type": Event.Type.ACKNOWLEDGE}))

        covered = event_covered_by_planned_maintenance(self.start_event)

        self.assertFalse(covered)

    def test_given_wrong_maxlevel_return_false(self):
        self.current_pm.filters.add(FilterFactory(filter={"maxlevel": 1}))

        covered = event_covered_by_planned_maintenance(self.start_event)

        self.assertFalse(covered)

    def test_given_pm_with_multiple_filters_only_matching_one_filter_return_false(self):
        self.current_pm.filters.add(FilterFactory(filter={"maxlevel": 1}))
        self.current_pm.filters.add(FilterFactory(filter={"event_type": Event.Type.INCIDENT_START}))

        covered = event_covered_by_planned_maintenance(self.start_event)

        self.assertFalse(covered)

    def test_given_no_pms_active_at_time_return_false(self):
        now = timezone.now()
        past_pm = PlannedMaintenanceFactory(start_time=now - timedelta(days=5), end_time=now - timedelta(days=4))
        past_pm.filters.add(self.maxlevel_filter)

        covered = event_covered_by_planned_maintenance(
            self.start_event, PlannedMaintenanceTask.objects.filter(id=past_pm.id)
        )

        self.assertFalse(covered)


@tag("database")
class TestConnectIncidentWithPlannedMaintenanceTasks(TestCase):
    def setUp(self):
        disconnect_signals()

        default_level = 3
        self.incident = StatefulIncidentFactory(level=default_level)

        self.hitting_filter = FilterFactory(filter={"maxlevel": default_level})
        self.covering_pm = PlannedMaintenanceFactory()
        self.covering_pm.filters.add(self.hitting_filter)

        self.not_hitting_filter = FilterFactory(filter={"maxlevel": 1})
        self.not_covering_pm = PlannedMaintenanceFactory()
        self.not_covering_pm.filters.add(self.not_hitting_filter)

    def teardown(self):
        connect_signals()

    def test_given_incident_with_fitting_pms_connects_them(self):
        connect_incident_with_planned_maintenance_tasks(incident=self.incident)

        ids = self.incident.planned_maintenance_tasks.values_list("id", flat=True)

        self.assertIn(self.covering_pm.id, ids)
        self.assertNotIn(self.not_covering_pm.id, ids)

    def test_given_closed_incident_does_nothing(self):
        closed_incident = StatefulIncidentFactory(end_time=timezone.now())

        connect_incident_with_planned_maintenance_tasks(incident=closed_incident)

        self.assertFalse(closed_incident.planned_maintenance_tasks.exists())

    def test_given_past_planned_maintenance_tasks_does_nothing(self):
        now = timezone.now()
        past_pm = PlannedMaintenanceFactory(start_time=now - timedelta(days=5), end_time=now - timedelta(days=4))

        connect_incident_with_planned_maintenance_tasks(
            incident=self.incident, pm_tasks=PlannedMaintenanceTask.objects.filter(id=past_pm.id)
        )

        self.assertFalse(self.incident.planned_maintenance_tasks.exists())
