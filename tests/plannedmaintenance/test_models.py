from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, tag
from django.utils import timezone

from argus.filter.factories import FilterFactory
from argus.incident.factories import StatefulIncidentFactory
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.plannedmaintenance.models import MODIFICATION_WINDOW_PM, PlannedMaintenanceTask
from argus.util.testing import disconnect_signals, connect_signals


@tag("database")
class PlannedMaintenanceQuerySetTests(TestCase):
    def setUp(self):
        disconnect_signals()

        now = timezone.now()
        self.future_pm = PlannedMaintenanceFactory(start_time=now + timedelta(days=1))
        self.current_pm = PlannedMaintenanceFactory(start_time=now - timedelta(minutes=5))
        self.past_pm = PlannedMaintenanceFactory(start_time=now - timedelta(days=1), end_time=now - timedelta(hours=12))

    def tearDown(self):
        connect_signals()

    def test_future_returns_only_pms_with_start_time_in_future(self):
        future_pms = PlannedMaintenanceTask.objects.future()

        self.assertNotIn(self.current_pm, future_pms)
        self.assertNotIn(self.past_pm, future_pms)
        self.assertIn(self.future_pm, future_pms)

    def test_past_returns_only_pms_with_end_time_in_past(self):
        past_pms = PlannedMaintenanceTask.objects.past()

        self.assertNotIn(self.current_pm, past_pms)
        self.assertNotIn(self.future_pm, past_pms)
        self.assertIn(self.past_pm, past_pms)

    def test_current_returns_only_pms_with_start_time_in_past_and_end_time_in_future(self):
        current_pms = PlannedMaintenanceTask.objects.current()

        self.assertNotIn(self.future_pm, current_pms)
        self.assertNotIn(self.past_pm, current_pms)
        self.assertIn(self.current_pm, current_pms)

    def test_active_at_time_returns_only_pms_with_start_time_before_and_end_time_after(self):
        active_at_time_pms = PlannedMaintenanceTask.objects.active_at_time(
            self.future_pm.start_time + timedelta(minutes=1)
        )

        self.assertNotIn(self.past_pm, active_at_time_pms)
        self.assertIn(self.future_pm, active_at_time_pms)
        self.assertIn(self.current_pm, active_at_time_pms)

    def test_started_after_time_returns_only_open_pms_with_start_time_between_given_time_and_now(self):
        recently_started_closed_pm = PlannedMaintenanceFactory(
            start_time=self.current_pm.start_time, end_time=self.current_pm.start_time + timedelta(seconds=15)
        )
        started_after_time_pms = PlannedMaintenanceTask.objects.started_after_time(
            self.current_pm.start_time - timedelta(minutes=1)
        )

        self.assertNotIn(self.past_pm, started_after_time_pms)
        self.assertIn(self.current_pm, started_after_time_pms)
        self.assertNotIn(self.future_pm, started_after_time_pms)
        self.assertNotIn(recently_started_closed_pm, started_after_time_pms)

    def ended_after_time_returns_only_closed_pms_with_end_time_after_time(self):
        recently_started_closed_pm = PlannedMaintenanceFactory(
            start_time=self.current_pm.start_time, end_time=self.current_pm.start_time + timedelta(seconds=15)
        )
        ended_after_time_pms = PlannedMaintenanceTask.objects.ended_after_time(
            self.current_pm.start_time - timedelta(minutes=1)
        )

        self.assertNotIn(self.past_pm, ended_after_time_pms)
        self.assertNotIn(self.current_pm, ended_after_time_pms)
        self.assertIn(self.future_pm, ended_after_time_pms)
        self.assertNotIn(recently_started_closed_pm, ended_after_time_pms)


@tag("database")
class PlannedMaintenanceTaskTests(TestCase):
    def setUp(self):
        disconnect_signals()

        now = timezone.now()
        self.future_pm = PlannedMaintenanceFactory(start_time=now + timedelta(days=1))
        self.current_pm = PlannedMaintenanceFactory(start_time=now - timedelta(minutes=5))
        self.past_pm = PlannedMaintenanceFactory(
            start_time=timezone.now() - MODIFICATION_WINDOW_PM - timedelta(hours=2),
            end_time=timezone.now() - MODIFICATION_WINDOW_PM - timedelta(hours=1),
        )

    def tearDown(self):
        connect_signals()

    def test_given_open_pm_task_modifiable_is_true(self):
        self.assertTrue(self.current_pm.modifiable)

    def test_given_recently_ended_pm_task_modifiable_is_true(self):
        open_pm_task = PlannedMaintenanceFactory(
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now(),
        )

        self.assertTrue(open_pm_task.modifiable)

    def test_given_long_ago_ended_pm_task_modifiable_is_false(self):
        self.assertFalse(self.past_pm.modifiable)

    def test_unmodifiable_pm_cannot_be_edited(self):
        pm = self.past_pm
        original_description = pm.description
        pm.description = "New description"
        with self.assertRaises(ValidationError):
            pm.save()

        pm.refresh_from_db()
        self.assertEqual(pm.description, original_description)

    def test_modifiable_pm_can_be_edited(self):
        pm = self.current_pm
        pm.description = "Updated description"
        pm.save()

        pm.refresh_from_db()
        self.assertEqual(pm.description, "Updated description")

    def test_given_active_pm_current_is_true(self):
        pm = PlannedMaintenanceFactory(start_time=timezone.now() - timedelta(minutes=5))
        self.assertTrue(pm.current)

    def test_given_past_pm_current_is_false(self):
        now = timezone.now()
        pm = PlannedMaintenanceFactory(start_time=now - timedelta(days=1), end_time=now - timedelta(hours=12))
        self.assertFalse(pm.current)

    def test_given_future_pm_current_is_false(self):
        pm = PlannedMaintenanceFactory(start_time=timezone.now() + timedelta(days=1))
        self.assertFalse(pm.current)

    def test_given_future_pm_cancel_deletes_task(self):
        pm_id = self.future_pm.id
        self.future_pm.cancel()

        self.assertFalse(PlannedMaintenanceTask.objects.filter(id=pm_id).exists())

    def test_given_past_pm_cancel_does_nothing(self):
        past_end_time = self.past_pm.end_time
        self.past_pm.cancel()
        self.past_pm.refresh_from_db()

        self.assertEqual(self.past_pm.end_time, past_end_time)

    def test_given_current_pm_cancel_sets_end_time(self):
        current_pm_end_time = self.current_pm.end_time
        self.current_pm.cancel()
        self.current_pm.refresh_from_db()

        self.assertNotEqual(self.current_pm.end_time, current_pm_end_time)
        self.assertLess(self.current_pm.end_time, timezone.now())

    def test_given_task_has_not_started_then_can_modify_start_time(self):
        new_start = self.future_pm.start_time + timedelta(hours=1)
        self.future_pm.start_time = new_start
        self.future_pm.save()
        self.future_pm.refresh_from_db()
        self.assertEqual(self.future_pm.start_time, new_start)

    def test_given_task_has_already_started_then_cannot_modify_start_time(self):
        original_start = self.current_pm.start_time
        self.current_pm.start_time = timezone.now() + timedelta(hours=1)
        with self.assertRaises(ValidationError):
            self.current_pm.save()
        self.current_pm.refresh_from_db()
        self.assertEqual(self.current_pm.start_time, original_start)

    def test_given_task_has_recently_ended_then_cannot_modify_start_time(self):
        now = timezone.now()
        recently_ended_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(minutes=5),
        )
        original_start = recently_ended_pm.start_time
        recently_ended_pm.start_time = now + timedelta(hours=1)
        with self.assertRaises(ValidationError):
            recently_ended_pm.save()
        recently_ended_pm.refresh_from_db()
        self.assertEqual(recently_ended_pm.start_time, original_start)


@tag("database")
class TestConnectCoveredIncidents(TestCase):
    def setUp(self):
        disconnect_signals()

        self.incident = StatefulIncidentFactory(level=2)
        self.incident2 = StatefulIncidentFactory(level=3)

        self.filter_maxlevel_2 = FilterFactory(filter={"maxlevel": 2})
        self.pm_maxlevel_2 = PlannedMaintenanceFactory()
        self.pm_maxlevel_2.filters.add(self.filter_maxlevel_2)

    def tearDown(self):
        connect_signals()

    def test_given_pm_without_connected_incidents_then_connect_new_incidents_that_are_covered(self):
        self.pm_maxlevel_2.connect_covered_incidents()

        self.assertIn(self.incident, self.pm_maxlevel_2.incidents.all())
        self.assertNotIn(self.incident2, self.pm_maxlevel_2.incidents.all())

    def test_given_pm_with_connected_incidents_then_do_not_remove_those_incidents(self):
        self.pm_maxlevel_2.incidents.add(self.incident)

        self.pm_maxlevel_2.connect_covered_incidents()

        self.assertIn(self.incident, self.pm_maxlevel_2.incidents.all())
        self.assertNotIn(self.incident2, self.pm_maxlevel_2.incidents.all())

    def test_given_pm_with_connected_incidents_and_new_covered_incidents_then_add_covered_incidents(self):
        filter_maxlevel_3 = FilterFactory(filter={"maxlevel": 3})
        pm_maxlevel_3 = PlannedMaintenanceFactory()
        pm_maxlevel_3.filters.add(filter_maxlevel_3)
        pm_maxlevel_3.incidents.add(self.incident)

        pm_maxlevel_3.connect_covered_incidents()

        self.assertIn(self.incident, pm_maxlevel_3.incidents.all())
        self.assertIn(self.incident2, pm_maxlevel_3.incidents.all())

    def test_given_pm_with_connected_incidents_and_replaced_filter_then_reset_covered_incidents(self):
        filter_maxlevel_3 = FilterFactory(filter={"maxlevel": 3})
        pm_maxlevel_3 = PlannedMaintenanceFactory()
        pm_maxlevel_3.filters.add(filter_maxlevel_3)

        # Call it once to sync incidents
        pm_maxlevel_3.connect_covered_incidents()

        self.assertIn(self.incident, pm_maxlevel_3.incidents.all())
        self.assertIn(self.incident2, pm_maxlevel_3.incidents.all())

        # Replace filter of PM
        pm_maxlevel_3.filters.remove(filter_maxlevel_3)
        pm_maxlevel_3.filters.add(self.filter_maxlevel_2)

        # Call it again to sync incidents anew
        pm_maxlevel_3.connect_covered_incidents()

        self.assertIn(self.incident, pm_maxlevel_3.incidents.all())
        self.assertNotIn(self.incident2, pm_maxlevel_3.incidents.all())

    def test_given_pm_with_connected_incident_that_was_closed_then_remove_incident_from_connected_incidents(self):
        self.pm_maxlevel_2.incidents.add(self.incident)
        self.incident.set_end(actor=self.incident.source.user)

        self.pm_maxlevel_2.connect_covered_incidents()

        self.assertNotIn(self.incident, self.pm_maxlevel_2.incidents.all())
        self.assertNotIn(self.incident2, self.pm_maxlevel_2.incidents.all())
