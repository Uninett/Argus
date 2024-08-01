from django.test import TestCase, tag

from argus.incident.factories import SourceSystemFactory, SourceUserFactory, TagFactory
from argus.incident.models import Incident
from argus.filter.queryset_filters import (
    QuerySetFilter,
    _incidents_fitting_maxlevel,
    _incidents_fitting_tristates,
    _incidents_with_source_systems,
    _incidents_with_tags,
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
        source_user3 = SourceUserFactory()
        source3 = SourceSystemFactory(user=source_user3)
        self.assertFalse(_incidents_with_source_systems(self.all_incidents, {"sourceSystemIds": [source3.pk]}))

    def test_incidents_with_source_systems_finds_incidents_with_these_source_systems(self):
        source1_filtered_incidents = list(
            _incidents_with_source_systems(self.all_incidents, {"sourceSystemIds": [self.source1.pk]})
        )
        self.assertIn(self.incident1, source1_filtered_incidents)
        self.assertNotIn(self.incident2, source1_filtered_incidents)

    def test_incidents_with_tags_empty_if_no_incidents_with_these_tags(self):
        tag4 = TagFactory()
        self.assertFalse(_incidents_with_tags(self.all_incidents, {"tags": [str(tag4)]}))

    def test_incidents_with_tags_finds_incidents_with_these_tags(self):
        tags1_filtered_incidents = list(_incidents_with_tags(self.all_incidents, {"tags": [str(self.tag1)]}))
        self.assertIn(self.incident1, tags1_filtered_incidents)
        self.assertNotIn(self.incident2, tags1_filtered_incidents)

    def test_incidents_fitting_tristates_empty_if_no_incidents_with_these_tristates(self):
        self.assertFalse(_incidents_fitting_tristates(self.all_incidents, {"stateful": True}))

    def test_incidents_fitting_tristates_finds_incidents_with_these_tristates(self):
        stateless_filtered_incidents = list(_incidents_fitting_tristates(self.all_incidents, {"stateful": False}))
        self.assertIn(self.incident1, stateless_filtered_incidents)
        self.assertIn(self.incident2, stateless_filtered_incidents)

    def test_incidents_fitting_maxlevel_empty_if_no_incidents_with_this_maxlevel(self):
        self.incident1.level = 5
        self.incident1.save(update_fields=["level"])
        self.incident2.level = 5
        self.incident2.save(update_fields=["level"])

        self.assertFalse(_incidents_fitting_maxlevel(self.all_incidents, {"maxlevel": 1}))

    def test_incidents_fitting_maxlevel_finds_incidents_with_this_maxlevel(self):
        maxlevel_filtered_incidents = list(_incidents_fitting_maxlevel(self.all_incidents, {"maxlevel": 5}))
        self.assertIn(self.incident1, maxlevel_filtered_incidents)
        self.assertIn(self.incident2, maxlevel_filtered_incidents)


@tag("database", "queryset-filter")
class FilteredIncidentsTests(TestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()

    def teardown(self):
        connect_signals()

    def test_filtered_incidents_returns_empty_if_no_incident_fits_filter(self):
        self.assertEqual(set(QuerySetFilter.filtered_incidents(dict())), set())

    def test_filtered_incidents_returns_incident_if_incident_fits_filter(self):
        self.assertEqual(
            set(QuerySetFilter.filtered_incidents({"sourceSystemIds": [self.source1.pk]})), {self.incident1}
        )
        self.assertEqual(
            set(QuerySetFilter.filtered_incidents({"sourceSystemIds": [self.source2.pk]})), {self.incident2}
        )

        self.assertEqual(set(QuerySetFilter.filtered_incidents({"tags": [str(self.tag1)]})), {self.incident1})
        self.assertEqual(set(QuerySetFilter.filtered_incidents({"tags": [str(self.tag2)]})), {self.incident2})

        self.assertEqual(
            set(QuerySetFilter.filtered_incidents({"sourceSystemIds": [self.source1.pk], "tags": [str(self.tag1)]})),
            {self.incident1},
        )
