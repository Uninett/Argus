from datetime import datetime
from random import choice
import unittest
from unittest.mock import Mock

from django.test import TestCase, tag, override_settings
from django.utils.dateparse import parse_datetime, parse_time
from django.utils.timezone import make_aware

from argus.incident.models import Incident
from argus.notificationprofile.models import (
    FilterWrapper,
    TimeRecurrence,
)
from argus.notificationprofile.factories import (
    TimeslotFactory,
    TimeRecurrenceFactory,
    FilterFactory,
)
from argus.util.testing import disconnect_signals, connect_signals

from . import IncidentAPITestCaseHelper


def set_time(timestamp: datetime, new_time: str):
    new_time = parse_time(new_time)
    return timestamp.replace(
        hour=new_time.hour,
        minute=new_time.minute,
        second=new_time.second,
        microsecond=new_time.microsecond,
    )


@tag("unittest")
class FilterWrapperTristatesEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A tristate must be one of True, False, None
    # "None" is equivalent to the tristate not being mentioned in the filter at all

    def test_are_tristates_empty_ignores_garbage(self):
        garbage_filter = FilterWrapper({"unknown-state": True})
        result = garbage_filter.are_tristates_empty()
        self.assertTrue(result)

    def test_are_tristates_empty_is_false(self):
        # tristate == None is equivalent to tristate missing from dict
        empty_filter = FilterWrapper({})
        result = empty_filter.are_tristates_empty()
        self.assertTrue(result)
        empty_filter2 = FilterWrapper({"open": None})
        result = empty_filter2.are_tristates_empty()
        self.assertTrue(result)

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": False})
    def test_are_tristates_empty_with_fallback(self):
        from django.conf import settings

        self.assertEqual(
            {"acked": False}, getattr(settings, "ARGUS_FALLBACK_FILTER", {}), "Test hasn't updated settings"
        )
        empty_filter = FilterWrapper({})
        result = empty_filter.are_tristates_empty()
        self.assertFalse(result)

    def test_are_tristates_empty_is_true(self):
        filter = FilterWrapper({"open": False})
        result = filter.are_tristates_empty()
        self.assertFalse(result)
        filter2 = FilterWrapper({"open": True})
        result = filter2.are_tristates_empty()
        self.assertFalse(result)


@tag("unittest")
class FilterWrapperIncidentFitsTristatesTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A tristate must be one of True, False, None
    # "None" is equivalent to the tristate not being mentioned in the filter at all

    def test_incident_fits_tristates_no_tristates_set(self):
        incident = Mock()
        empty_filter = FilterWrapper({})
        result = empty_filter.incident_fits_tristates(incident)
        self.assertEqual(result, None)

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": True})
    def test_incident_fits_tristates_no_tristates_set_with_fallback(self):
        incident = Mock()
        # Shouldn't match
        incident.acked = False
        empty_filter = FilterWrapper({})
        result = empty_filter.incident_fits_tristates(incident)
        self.assertEqual(result, False)
        # Should match
        incident.acked = True
        empty_filter = FilterWrapper({})
        result = empty_filter.incident_fits_tristates(incident)
        self.assertEqual(result, True)

    def test_incident_fits_tristates_is_true(self):
        incident = Mock()
        incident.open = True
        incident.acked = False
        incident.stateful = True
        empty_filter = FilterWrapper({"open": True, "acked": False})
        result = empty_filter.incident_fits_tristates(incident)
        self.assertTrue(result)

    def test_incident_fits_tristates_is_false(self):
        incident = Mock()
        incident.open = True
        incident.acked = False
        incident.stateful = True
        empty_filter = FilterWrapper({"open": False, "acked": False})
        result = empty_filter.incident_fits_tristates(incident)
        self.assertFalse(result)

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": True})
    def test_incident_fits_tristates_fallback_should_not_override(self):
        incident = Mock()
        # Should match
        incident.acked = False
        filter = FilterWrapper({"acked": False})
        result = filter.incident_fits_tristates(incident)
        self.assertEqual(result, True)


@tag("unittest")
class FilterWrapperMaxlevelEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A maxlevel must be one of the integers in Incident.LEVELS if it is set at all.

    def test_is_maxlevel_empty_is_false(self):
        empty_filter = FilterWrapper({})
        result = empty_filter.is_maxlevel_empty()
        self.assertTrue(result)

    def test_is_maxlevel_empty_is_true(self):
        empty_filter = FilterWrapper({"maxlevel": "whatever"})
        result = empty_filter.is_maxlevel_empty()
        self.assertFalse(result)


@tag("unittest")
class FilterWrapperIncidentFitsMaxlevelTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A maxlevel must be one of the integers in Incident.LEVELS if it is set at all.

    def test_incident_fits_maxlevel_no_maxlevel_set(self):
        incident = Mock()
        empty_filter = FilterWrapper({})
        result = empty_filter.incident_fits_maxlevel(incident)
        self.assertEqual(result, None)

    def test_incident_fits_maxlevel(self):
        incident = Mock()
        level = choice(Incident.LEVELS)
        maxlevel = choice(Incident.LEVELS)
        incident.level = level
        filter = FilterWrapper({"maxlevel": maxlevel})
        result = filter.incident_fits_maxlevel(incident)
        self.assertEqual(result, level <= maxlevel)


@tag("unittest")
class HelperTimeFunctionsTests(TestCase):
    def test_set_time_works(self):
        self.assertEqual(parse_datetime("2000-01-01 10:00"), set_time(parse_datetime("2000-01-01 00:00"), "10:00"))

    def test_make_aware_function_works(self):
        self.assertEqual(make_aware(parse_datetime("2019-11-25 00:00")).strftime("%A"), "Monday")


@tag("database")
class TimeRecurrenceTests(TestCase, IncidentAPITestCaseHelper):
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

    def teardown(self):
        connect_signals()

    def test_timestamp_is_within_false_if_before_recurrence(self):
        self.assertFalse(self.recurrence1.timestamp_is_within(set_time(self.monday_datetime, "00:29:01")))

    def test_timestamp_is_within_true_if_within_recurrence(self):
        self.assertTrue(self.recurrence1.timestamp_is_within(set_time(self.monday_datetime, "00:30:00")))
        self.assertTrue(self.recurrence1.timestamp_is_within(set_time(self.monday_datetime, "00:30:01")))

    def test_timestamp_is_within_false_if_after_recurrence(self):
        self.assertFalse(self.recurrence1.timestamp_is_within(set_time(self.monday_datetime, "00:30:02")))


@tag("database")
class TimeslotTests(TestCase, IncidentAPITestCaseHelper):
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

    def teardown(self):
        connect_signals()

    def test_timestamp_is_within_recurrences_true_if_within_recurrences(self):
        self.assertTrue(self.timeslot1.timestamp_is_within_time_recurrences(set_time(self.monday_datetime, "00:30:01")))
        self.assertTrue(self.timeslot1.timestamp_is_within_time_recurrences(set_time(self.monday_datetime, "00:30:03")))

    def test_timestamp_is_within_recurrences_false_if_not_within_recurrences(self):
        self.assertFalse(
            self.timeslot1.timestamp_is_within_time_recurrences(set_time(self.monday_datetime, "00:30:02"))
        )


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
            filter_string='{"sourceSystemIds": []}',
        )
        self.filter_source1 = FilterFactory(
            user=self.user1,
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.filter_source2 = FilterFactory(
            user=self.user1,
            filter_string=f'{{"sourceSystemIds": [{self.source2.pk}]}}',
        )
        self.filter_no_tags = FilterFactory(
            user=self.user1,
            filter_string='{"tags": []}',
        )
        self.filter_tags1 = FilterFactory(
            user=self.user1,
            filter_string=f'{{"tags": ["{self.tag1}"]}}',
        )
        self.filter_tags2 = FilterFactory(
            user=self.user1,
            filter_string=f'{{"tags": ["{self.tag2}"]}}',
        )
        self.filter_no_source_no_tags = FilterFactory(
            user=self.user1,
            filter_string='{"sourceSystemIds": [], "tags": []}',
        )
        self.filter_source1_tags1 = FilterFactory(
            user=self.user1,
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}], "tags": ["{self.tag1}"]}}',
        )

    def teardown(self):
        connect_signals()

    def test_source_fits_true_if_incident_fits_source(self):
        self.assertTrue(self.filter_source1.source_system_fits(self.incident1))

    def test_source_fits_false_if_incident_does_not_fit_source(self):
        self.assertFalse(self.filter_no_source.source_system_fits(self.incident1))
        self.assertFalse(self.filter_source2.source_system_fits(self.incident1))

    def test_tags_fit_true_if_incident_fits_tags(self):
        self.assertTrue(self.filter_tags1.tags_fit(self.incident1))

    def test_source_fits_false_if_incident_does_not_fit_tags(self):
        self.assertFalse(self.filter_no_tags.tags_fit(self.incident1))
        self.assertFalse(self.filter_tags2.tags_fit(self.incident1))

    def test_tags_fit_true_if_incident_fits_source_and_tags(self):
        self.assertTrue(self.filter_source1_tags1.incident_fits(self.incident1))

    def test_tags_fit_false_if_incident_does_not_fit_source_and_tags(self):
        self.assertFalse(self.filter_no_source_no_tags.incident_fits(self.incident1))
        self.assertFalse(self.filter_source1_tags1.incident_fits(self.incident2))

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
