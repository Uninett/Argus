from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from argus.filter.factories import FilterFactory
from argus.incident.factories import StatefulIncidentFactory
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.util.datetime_utils import LOCAL_INFINITY
from argus.util.testing import connect_signals, disconnect_signals


class CheckEndedMaintenanceTests(TestCase):
    def setUp(self):
        disconnect_signals()

        now = timezone.now()

        self.open_filter = FilterFactory(filter={"open": True})
        self.incident = self.incident = StatefulIncidentFactory(start_time=now - timedelta(days=1))

        self.future_pm = PlannedMaintenanceFactory(
            start_time=now + timedelta(days=1),
            end_time=LOCAL_INFINITY,
        )
        self.current_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(hours=1),
            end_time=LOCAL_INFINITY,
        )
        self.recently_ended_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(days=2),
            end_time=now,
        )
        self.past_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=1),
        )

        self.future_pm.filters.add(self.open_filter)
        self.current_pm.filters.add(self.open_filter)
        self.past_pm.filters.add(self.open_filter)

        self.future_pm.incidents.add(self.incident)
        self.current_pm.incidents.add(self.incident)
        self.recently_ended_pm.incidents.add(self.incident)
        self.past_pm.incidents.add(self.incident)

    def tearDown(self):
        connect_signals()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "check_ended_maintenance",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_given_recently_ended_pm_then_remove_linked_incidents(self):
        out = self.call_command()

        self.assertFalse(out)
        self.assertFalse(self.recently_ended_pm.incidents.exists())

    def test_given_long_ended_pm_with_linked_incidents_then_remove_linked_incidents(self):
        out = self.call_command()

        self.assertFalse(out)
        self.assertFalse(self.past_pm.incidents.exists())

    def test_given_ongoing_pm_then_do_not_remove_linked_incidents(self):
        out = self.call_command()

        self.assertFalse(out)
        self.assertTrue(self.current_pm.incidents.exists())

    def test_given_future_pm_then_do_not_remove_linked_incidents(self):
        out = self.call_command()

        self.assertFalse(out)
        self.assertTrue(self.future_pm.incidents.exists())
