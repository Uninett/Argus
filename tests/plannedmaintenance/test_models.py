from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.incident.factories import IncidentFactory, SourceSystemFactory
from argus.plannedmaintenance.models import MODIFICATION_WINDOW_PM, PlannedMaintenanceTask
from argus.util.testing import disconnect_signals, connect_signals


@tag("database")
class PlannedMaintenanceTaskTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.user = PersonUserFactory()
        self.source = SourceSystemFactory(name="foobar")
        self.zero_filter = FilterFactory(user=self.user, filter={"sourceSystemIds": [0]})
        self.source_filter = FilterFactory(user=self.user, filter={"sourceSystemIds": [self.source.id]})

    def teardown(self):
        connect_signals()

    def test_given_open_pm_task_modifiable_is_true(self):
        open_pm_task = PlannedMaintenanceTask(owner=self.user)

        self.assertTrue(open_pm_task.modifiable)

    def test_given_recently_ended_pm_task_modifiable_is_true(self):
        open_pm_task = PlannedMaintenanceTask(
            owner=self.user,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now(),
        )

        self.assertTrue(open_pm_task.modifiable)

    def test_given_long_ago_ended_pm_task_modifiable_is_false(self):
        open_pm_task = PlannedMaintenanceTask(
            owner=self.user,
            start_time=timezone.now() - MODIFICATION_WINDOW_PM - timedelta(hours=2),
            end_time=timezone.now() - MODIFICATION_WINDOW_PM - timedelta(hours=1),
        )

        self.assertFalse(open_pm_task.modifiable)

    def test_covers_relevant_incident(self):
        pm_task = PlannedMaintenanceTask(
            owner=self.user,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
        )
        pm_task.save()
        pm_task.filters.add(self.source_filter)

        incident = IncidentFactory(
            start_time=timezone.now() - timedelta(minutes=30),
            end_time=timezone.now() + timedelta(minutes=30),
            source=self.source,
        )
        self.assertTrue(pm_task.covers_incident(incident))

    def test_does_not_cover_chronologically_irrelevant_incident(self):
        pm_task = PlannedMaintenanceTask(
            owner=self.user,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
        )
        pm_task.save()
        pm_task.filters.add(self.source_filter)

        incident1 = IncidentFactory(
            start_time=timezone.now() + timedelta(hours=2),
            source=self.source,
        )
        self.assertFalse(pm_task.covers_incident(incident1))

        incident2 = IncidentFactory(
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() - timedelta(hours=1),
            source=self.source,
        )
        self.assertFalse(pm_task.covers_incident(incident2))

    def test_does_not_cover_incident_outside_filter(self):
        pm_task = PlannedMaintenanceTask(
            owner=self.user,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
        )
        pm_task.save()
        pm_task.filters.add(self.zero_filter)

        incident = IncidentFactory(
            start_time=timezone.now() - timedelta(minutes=30),
            end_time=timezone.now() + timedelta(minutes=30),
            source=self.source,
        )
        self.assertFalse(pm_task.covers_incident(incident))
