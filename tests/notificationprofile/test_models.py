from datetime import datetime

from django.test import TestCase, tag
from django.utils.dateparse import parse_datetime, parse_time
from django.utils.timezone import make_aware

from argus.notificationprofile.models import TimeRecurrence
from argus.notificationprofile.factories import (
    TimeslotFactory,
    TimeRecurrenceFactory,
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
