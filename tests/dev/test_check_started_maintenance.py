from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from argus.filter.factories import FilterFactory
from argus.incident.factories import StatefulIncidentFactory
from argus.incident.models import Incident
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.plannedmaintenance.utils import incidents_covered_by_planned_maintenance_task
from argus.util.datetime_utils import LOCAL_INFINITY
from argus.util.testing import connect_signals, disconnect_signals


class CheckStartedMaintenanceTests(TestCase):
    def setUp(self):
        disconnect_signals()

        now = timezone.now()

        self.open_filter = FilterFactory(filter={"open": True})
        self.incident = StatefulIncidentFactory(start_time=now - timedelta(days=1))

        self.recently_started_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(minutes=1),
            end_time=LOCAL_INFINITY,
        )

        self.long_ago_started_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(days=2),
            end_time=LOCAL_INFINITY,
        )

        self.past_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=1),
        )

        self.future_pm = PlannedMaintenanceFactory(
            start_time=now + timedelta(days=1),
            end_time=LOCAL_INFINITY,
        )

        self.recently_started_pm.filters.add(self.open_filter)
        self.long_ago_started_pm.filters.add(self.open_filter)
        self.past_pm.filters.add(self.open_filter)
        self.future_pm.filters.add(self.open_filter)

    def tearDown(self):
        connect_signals()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "check_started_maintenance",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_given_recently_started_pm_then_link_incident(self):
        out = self.call_command()

        self.assertFalse(out)
        incidents = incidents_covered_by_planned_maintenance_task(
            queryset=Incident.objects.all(), pm_task=self.recently_started_pm
        )
        self.assertIn(self.incident, incidents)

    def test_given_long_ago_started_pm_then_link_incident(self):
        out = self.call_command()

        self.assertFalse(out)
        incidents = incidents_covered_by_planned_maintenance_task(
            queryset=Incident.objects.all(), pm_task=self.long_ago_started_pm
        )
        self.assertIn(self.incident, incidents)

    def test_given_past_pm_then_do_not_link_incident(self):
        out = self.call_command()

        self.assertFalse(out)
        self.assertFalse(self.past_pm.incidents.exists())

    def test_given_future_pm_then_do_not_link_incident(self):
        out = self.call_command()

        self.assertFalse(out)
        self.assertFalse(self.future_pm.incidents.exists())
