from django.test import TestCase, tag
from django.utils.dateparse import parse_datetime, parse_time
from django.utils.timezone import make_aware

from argus.filter.factories import FilterFactory
from argus.incident.factories import SourceSystemFactory, TagFactory
from argus.notificationprofile.models import TimeRecurrence
from argus.notificationprofile.factories import (
    TimeslotFactory,
    TimeRecurrenceFactory,
)
from argus.util.testing import disconnect_signals, connect_signals

from tests.notificationprofile import IncidentAPITestCaseHelper


@tag("database")
class FilterTests(TestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()
        self.monday_datetime = make_aware(parse_datetime("2019-11-25 00:00"))

        self.timeslot1 = TimeslotFactory(
            user=self.user1,
            name="Test",
        )
        self.recurrence1 = TimeRecurrenceFactory(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.MONDAY},
            start=parse_time("00:30:00"),
            end=parse_time("00:30:01"),
        )
        self.recurrence2 = TimeRecurrenceFactory(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.MONDAY},
            start=parse_time("00:30:03"),
            end=parse_time("00:31"),
        )
        self.recurrence_all_day = TimeRecurrenceFactory(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.TUESDAY},
            start=TimeRecurrence.DAY_START,
            end=TimeRecurrence.DAY_END,
        )

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

    def teardown(self):
        connect_signals()

    def test_incidents_with_source_systems_empty_if_no_incidents_with_these_source_systems(self):
        source3 = SourceSystemFactory()
        filter_source3 = FilterFactory(
            user=self.user1,
            filter={"sourceSystemIds": [source3.pk]},
        )
        self.assertFalse(filter_source3.incidents_with_source_systems())

    def test_incidents_with_source_systems_finds_incidents_with_these_source_systems(self):
        source1_filtered_incidents = list(self.filter_source1.incidents_with_source_systems())
        self.assertIn(self.incident1, source1_filtered_incidents)
        self.assertNotIn(self.incident2, source1_filtered_incidents)

    def test_incidents_with_tags_empty_if_no_incidents_with_these_tags(self):
        tag4 = TagFactory()
        filter_tag4 = FilterFactory(
            user=self.user1,
            filter={"tags": [str(tag4)]},
        )
        self.assertFalse(filter_tag4.incidents_with_tags())

    def test_incidents_with_tags_finds_incidents_with_these_tags(self):
        tags1_filtered_incidents = list(self.filter_tags1.incidents_with_tags())
        self.assertIn(self.incident1, tags1_filtered_incidents)
        self.assertNotIn(self.incident2, tags1_filtered_incidents)

    def test_incidents_fitting_tristates_empty_if_no_incidents_with_these_tristates(self):
        filter_stateful = FilterFactory(
            user=self.user1,
            filter={"stateful": True},
        )

        self.assertFalse(filter_stateful.incidents_fitting_tristates())

    def test_incidents_fitting_tristates_finds_incidents_with_these_tristates(self):
        filter_stateless = FilterFactory(
            user=self.user1,
            filter={"stateful": False},
        )
        stateless_filtered_incidents = list(filter_stateless.incidents_fitting_tristates())
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

        self.assertFalse(filter_maxlevel1.incidents_fitting_maxlevel())

    def test_incidents_fitting_maxlevel_finds_incidents_with_this_maxlevel(self):
        filter_maxlevel5 = FilterFactory(
            user=self.user1,
            filter={"maxlevel": 5},
        )
        maxlevel_filtered_incidents = list(filter_maxlevel5.incidents_fitting_maxlevel())
        self.assertIn(self.incident1, maxlevel_filtered_incidents)
        self.assertIn(self.incident2, maxlevel_filtered_incidents)

    def test_filtered_incidents_returns_empty_if_no_incident_fits_filter(self):
        self.assertEqual(set(self.filter_no_source.filtered_incidents), set())
        self.assertEqual(set(self.filter_no_tags.filtered_incidents), set())
        self.assertEqual(set(self.filter_no_source_no_tags.filtered_incidents), set())

    def test_filtered_incidents_returns_incident_if_incident_fits_filter(self):
        self.assertEqual(set(self.filter_source1.filtered_incidents), {self.incident1})
        self.assertEqual(set(self.filter_source2.filtered_incidents), {self.incident2})

        self.assertEqual(set(self.filter_tags1.filtered_incidents), {self.incident1})
        self.assertEqual(set(self.filter_tags2.filtered_incidents), {self.incident2})

        self.assertEqual(set(self.filter_source1_tags1.filtered_incidents), {self.incident1})
