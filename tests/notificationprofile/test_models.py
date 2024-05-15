from datetime import datetime
from random import choice
import unittest
from unittest.mock import Mock

from django.test import TestCase, tag, override_settings
from django.utils.dateparse import parse_datetime, parse_time
from django.utils.timezone import make_aware

from argus.incident.factories import SourceSystemFactory, TagFactory
from argus.incident.models import Event, Incident
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

    def test_get_incident_tristate_checks_no_tristates_set(self):
        incident = Mock()
        empty_filter = FilterWrapper({})
        result = empty_filter.get_incident_tristate_checks(incident)
        self.assertEqual(result, {})

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": True})
    def test_get_incident_tristate_checks_no_tristates_set_with_fallback(self):
        incident = Mock()
        # Shouldn't match
        incident.acked = False
        empty_filter = FilterWrapper({})
        result = empty_filter.get_incident_tristate_checks(incident)
        self.assertEqual(result["open"], None)
        self.assertEqual(result["acked"], False)
        self.assertEqual(result["stateful"], None)
        # Should match
        incident.acked = True
        empty_filter = FilterWrapper({})
        result = empty_filter.get_incident_tristate_checks(incident)
        self.assertNotIn(False, result.values())
        self.assertEqual(result["open"], None)
        self.assertEqual(result["acked"], True)
        self.assertEqual(result["stateful"], None)

    def test_get_incident_tristate_checks_is_true(self):
        incident = Mock()
        incident.open = True
        incident.acked = False
        incident.stateful = True
        filter = FilterWrapper({"open": True, "acked": False})
        result = filter.get_incident_tristate_checks(incident)
        self.assertTrue(set(result.values()))  # result not empty
        self.assertEqual(result["open"], True)
        self.assertEqual(result["acked"], True)
        self.assertEqual(result["stateful"], None)

    def test_get_incident_tristate_checks_is_false(self):
        incident = Mock()
        incident.open = True
        incident.acked = False
        incident.stateful = True
        filter = FilterWrapper({"open": False, "acked": False})
        result = filter.get_incident_tristate_checks(incident)
        self.assertIn(False, result.values())
        self.assertEqual(result["open"], False)
        self.assertEqual(result["acked"], True)
        self.assertEqual(result["stateful"], None)

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": True})
    def test_get_incident_tristate_checks_fallback_should_not_override(self):
        incident = Mock()
        # Should match
        incident.acked = False
        filter = FilterWrapper({"acked": False})
        result = filter.get_incident_tristate_checks(incident)
        self.assertNotIn(False, result.values())
        self.assertEqual(result["open"], None)
        self.assertEqual(result["acked"], True)
        self.assertEqual(result["stateful"], None)


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
class FilterWrapperEventTypeEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # An event type must be one of the types in Event.Type if it is set at all.

    def test_when_filter_is_empty_is_event_type_empty_should_return_true(self):
        empty_filter = FilterWrapper({})
        self.assertTrue(empty_filter.is_event_types_empty())

    def test_when_event_filter_exists_is_event_type_empty_should_return_false(self):
        empty_filter = FilterWrapper({"event_types": ["whatever"]})
        self.assertFalse(empty_filter.is_event_types_empty())


@tag("unittest")
class FilterWrapperIncidentFitsEventTypeTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # An event type must be one of the types in Event.Type if it is set at all.

    def test_when_event_filter_is_empty_any_event_should_fit(self):
        event = Mock()
        empty_filter = FilterWrapper({})
        self.assertEqual(empty_filter.event_fits(event), True)

    def test_when_event_filter_is_set_event_with_matching_type_should_fit(self):
        event = Mock()
        event_type = Event.Type.INCIDENT_CHANGE
        event.type = event_type
        filter = FilterWrapper({"event_types": [event_type]})
        self.assertTrue(filter.event_fits(event))

    def test_when_event_filter_is_set_event_with_not_matching_type_should_not_fit(self):
        event = Mock()
        event.type = Event.Type.INCIDENT_CHANGE
        filter = FilterWrapper({"event_types": [Event.Type.ACKNOWLEDGE]})
        self.assertFalse(filter.event_fits(event))


@tag("unittest")
class FilterWrapperSourceSystemIdsEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A sourceSystemId must be an integer if it is set at all.

    def test_when_filter_is_empty_are_source_system_ids_empty_should_return_true(self):
        empty_filter = FilterWrapper({})
        self.assertTrue(empty_filter.are_source_system_ids_empty())

    def test_when_source_system_ids_is_an_empty_list_are_source_system_ids_empty_should_return_true(self):
        empty_filter = FilterWrapper({"sourceSystemIds": []})
        self.assertTrue(empty_filter.are_source_system_ids_empty())

    def test_when_source_system_ids_filter_exists_are_source_system_ids_empty_should_return_false(self):
        empty_filter = FilterWrapper({"sourceSystemIds": [1]})
        self.assertFalse(empty_filter.are_source_system_ids_empty())


@tag("unittest")
class FilterWrapperTagsEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A tag must be a string of the format key=value if it is set at all.

    def test_when_filter_is_empty_are_tags_empty_should_return_true(self):
        empty_filter = FilterWrapper({})
        self.assertTrue(empty_filter.are_tags_empty())

    def test_when_tags_is_an_empty_list_are_tags_empty_should_return_true(self):
        empty_filter = FilterWrapper({"tags": []})
        self.assertTrue(empty_filter.are_tags_empty())

    def test_when_tags_filter_exists_are_tags_empty_should_return_false(self):
        empty_filter = FilterWrapper({"tags": ["a=b"]})
        self.assertFalse(empty_filter.are_tags_empty())


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
