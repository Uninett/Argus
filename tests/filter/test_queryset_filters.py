from django.test import TestCase, tag
from django.utils.dateparse import parse_datetime, parse_time
from django.utils.timezone import make_aware

from argus.filter.factories import FilterFactory
from argus.incident.factories import SourceSystemFactory, TagFactory
from argus.incident.models import Incident
from argus.filter.queryset_filters import (
    filtered_incidents,
    _incidents_fitting_maxlevel,
    _incidents_fitting_tristates,
    _incidents_with_source_systems,
    _incidents_with_tags,
)
from argus.notificationprofile.models import TimeRecurrence
from argus.notificationprofile.factories import (
    TimeslotFactory,
    TimeRecurrenceFactory,
)
from argus.util.testing import disconnect_signals, connect_signals

from tests.notificationprofile import IncidentAPITestCaseHelper


@tag("database", "queryset-filter")
class FilteredIncidentsHelpersTests(TestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()
        self.all_incidents = Incident.objects.all()

    def teardown(self):
        connect_signals()

    def test_incidents_with_source_systems_empty_if_no_incidents_with_these_source_systems(self):
        source3 = SourceSystemFactory()
        filter_source3 = FilterFactory(
            user=self.user1,
            filter={"sourceSystemIds": [source3.pk]},
        )
        self.assertFalse(_incidents_with_source_systems(filter_source3, self.all_incidents))

    def test_incidents_with_source_systems_finds_incidents_with_these_source_systems(self):
        filter_source1 = FilterFactory(
            user=self.user1,
            filter={"sourceSystemIds": [self.source1.pk]},
        )
        source1_filtered_incidents = list(_incidents_with_source_systems(filter_source1, self.all_incidents))
        self.assertIn(self.incident1, source1_filtered_incidents)
        self.assertNotIn(self.incident2, source1_filtered_incidents)

    def test_incidents_with_tags_empty_if_no_incidents_with_these_tags(self):
        tag4 = TagFactory()
        filter_tag4 = FilterFactory(
            user=self.user1,
            filter={"tags": [str(tag4)]},
        )
        self.assertFalse(_incidents_with_tags(filter_tag4, self.all_incidents))

    def test_incidents_with_tags_finds_incidents_with_these_tags(self):
        filter_tags1 = FilterFactory(
            user=self.user1,
            filter={"tags": [str(self.tag1)]},
        )
        tags1_filtered_incidents = list(_incidents_with_tags(filter_tags1, self.all_incidents))
        self.assertIn(self.incident1, tags1_filtered_incidents)
        self.assertNotIn(self.incident2, tags1_filtered_incidents)

    def test_incidents_fitting_tristates_empty_if_no_incidents_with_these_tristates(self):
        filter_stateful = FilterFactory(
            user=self.user1,
            filter={"stateful": True},
        )

        self.assertFalse(_incidents_fitting_tristates(filter_stateful, self.all_incidents))

    def test_incidents_fitting_tristates_finds_incidents_with_these_tristates(self):
        filter_stateless = FilterFactory(
            user=self.user1,
            filter={"stateful": False},
        )
        stateless_filtered_incidents = list(_incidents_fitting_tristates(filter_stateless, self.all_incidents))
        self.assertIn(self.incident1, stateless_filtered_incidents)
        self.assertIn(self.incident2, stateless_filtered_incidents)

    def test_incidents_fitting_maxlevel_empty_if_no_incidents_with_this_maxlevel(self):
        self.incident1.level = 5
        self.incident1.save(update_fields=["level"])
        self.incident2.level = 5
        self.incident2.save(update_fields=["level"])
        filter_maxlevel1 = FilterFactory(
            user=self.user1,
            filter={"maxlevel": 1},
        )

        self.assertFalse(_incidents_fitting_maxlevel(filter_maxlevel1, self.all_incidents))

    def test_incidents_fitting_maxlevel_finds_incidents_with_this_maxlevel(self):
        filter_maxlevel5 = FilterFactory(
            user=self.user1,
            filter={"maxlevel": 5},
        )
        maxlevel_filtered_incidents = list(_incidents_fitting_maxlevel(filter_maxlevel5, self.all_incidents))
        self.assertIn(self.incident1, maxlevel_filtered_incidents)
        self.assertIn(self.incident2, maxlevel_filtered_incidents)


@tag("database", "queryset-filter")
class FilteredIncidentsTests(TestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()
        self.filter_no_source = FilterFactory(
            user=self.user1,
            filter=dict(),
        )
        self.filter_source1 = FilterFactory(
            user=self.user1,
            filter={"sourceSystemIds": [self.source1.pk]},
        )
        self.filter_source2 = FilterFactory(
            user=self.user1,
            filter={"sourceSystemIds": [self.source2.pk]},
        )
        self.filter_no_tags = FilterFactory(
            user=self.user1,
            filter=dict(),
        )
        self.filter_tags1 = FilterFactory(
            user=self.user1,
            filter={"tags": [str(self.tag1)]},
        )
        self.filter_tags2 = FilterFactory(
            user=self.user1,
            filter={"tags": [str(self.tag2)]},
        )
        self.filter_no_source_no_tags = FilterFactory(
            user=self.user1,
            filter=dict(),
        )
        self.filter_source1_tags1 = FilterFactory(
            user=self.user1,
            filter={"sourceSystemIds": [self.source1.pk], "tags": [str(self.tag1)]},
        )
        self.all_incidents = Incident.objects.all()

    def teardown(self):
        connect_signals()

    def test_filtered_incidents_returns_empty_if_no_incident_fits_filter(self):
        self.assertEqual(set(filtered_incidents(self.filter_no_source)), set())
        self.assertEqual(set(filtered_incidents(self.filter_no_tags)), set())
        self.assertEqual(set(filtered_incidents(self.filter_no_source_no_tags)), set())

    def test_filtered_incidents_returns_incident_if_incident_fits_filter(self):
        self.assertEqual(set(filtered_incidents(self.filter_source1)), {self.incident1})
        self.assertEqual(set(filtered_incidents(self.filter_source2)), {self.incident2})

        self.assertEqual(set(filtered_incidents(self.filter_tags1)), {self.incident1})
        self.assertEqual(set(filtered_incidents(self.filter_tags2)), {self.incident2})

        self.assertEqual(set(filtered_incidents(self.filter_source1_tags1)), {self.incident1})
