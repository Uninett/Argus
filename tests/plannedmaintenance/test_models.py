from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, tag
from django.utils import timezone

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

    def teardown(self):
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

    def teardown(self):
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
