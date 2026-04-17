from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone

from argus.auth.factories import PersonUserFactory, SourceUserFactory
from argus.filter.filterwrapper import SpecialFilterKey
from argus.filter.queryset_filters import _incidents_fitting_special_filters
from argus.incident.factories import (
    SourceSystemFactory,
    StatefulIncidentFactory,
)
from argus.incident.models import Incident
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.util.testing import disconnect_signals, connect_signals


@tag("database", "queryset-filter")
class IncidentsFittingSpecialFiltersTests(TestCase):
    def setUp(self):
        disconnect_signals()
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(user=source_user)
        self.user = PersonUserFactory()
        self.now = timezone.now()

    def tearDown(self):
        connect_signals()

    def test_when_hide_closed_acked_is_true_then_it_should_exclude_closed_acked_incidents(self):
        closed_acked = StatefulIncidentFactory(source=self.source, end_time=self.now)
        closed_acked.create_ack(self.user)
        open_incident = StatefulIncidentFactory(source=self.source)

        qs = Incident.objects.all()
        result = _incidents_fitting_special_filters(qs, {SpecialFilterKey.HIDE_CLOSED_ACKED: True})
        self.assertNotIn(closed_acked, result)
        self.assertIn(open_incident, result)

    def test_when_under_maintenance_is_true_then_it_should_return_only_maintained_incidents(self):
        maintained = StatefulIncidentFactory(source=self.source)
        not_maintained = StatefulIncidentFactory(source=self.source)
        pm_task = PlannedMaintenanceFactory(
            start_time=self.now - timedelta(hours=1),
            end_time=self.now + timedelta(hours=1),
        )
        pm_task.incidents.add(maintained)

        qs = Incident.objects.all()
        result = _incidents_fitting_special_filters(qs, {SpecialFilterKey.UNDER_MAINTENANCE: True})
        self.assertIn(maintained, result)
        self.assertNotIn(not_maintained, result)

    def test_when_no_special_filters_then_it_should_return_all_incidents(self):
        StatefulIncidentFactory(source=self.source)
        StatefulIncidentFactory(source=self.source)

        qs = Incident.objects.all()
        result = _incidents_fitting_special_filters(qs, {})
        self.assertEqual(set(result), set(qs))
