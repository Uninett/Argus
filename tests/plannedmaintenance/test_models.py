from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.plannedmaintenance.models import MODIFICATION_WINDOW_PM, PlannedMaintenanceTask
from argus.util.testing import disconnect_signals, connect_signals


@tag("database")
class PlannedMaintenanceTaskTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.user = PersonUserFactory()

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
