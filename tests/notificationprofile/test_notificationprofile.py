from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_time
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase

from argus.auth.models import User
from argus.incident.models import (
    Incident,
    IncidentTagRelation,
    SourceSystem,
    SourceSystemType,
    Tag,
)
from argus.incident.serializers import IncidentSerializer
from ..incident import IncidentBasedAPITestCaseHelper
from argus.notificationprofile.models import (
    Filter,
    NotificationProfile,
    TimeRecurrence,
    Timeslot,
)
from argus.util.utils import duplicate
from argus.util.testing import disconnect_signals, connect_signals


class IncidentAPITestCaseHelper(IncidentBasedAPITestCaseHelper):
    def init_test_objects(self):
        super().init_test_objects()

        self.source_type2 = SourceSystemType.objects.create(name="type2")
        self.source2 = SourceSystem.objects.create(
            name="System 2",
            type=self.source_type2,
            user=User.objects.create(username="system_2"),
        )

        self.incident1 = Incident.objects.create(
            start_time=timezone.now(),
            source=self.source1,
            source_incident_id="123",
        )
        self.incident2 = duplicate(self.incident1, source=self.source2)

        self.tag1 = Tag.objects.create_from_tag("object=1")
        self.tag2 = Tag.objects.create_from_tag("object=2")
        self.tag3 = Tag.objects.create_from_tag("location=Oslo")

        IncidentTagRelation.objects.create(tag=self.tag1, incident=self.incident1, added_by=self.user1)
        IncidentTagRelation.objects.create(tag=self.tag3, incident=self.incident1, added_by=self.user1)
        IncidentTagRelation.objects.create(tag=self.tag2, incident=self.incident2, added_by=self.user1)
        IncidentTagRelation.objects.create(tag=self.tag3, incident=self.incident2, added_by=self.user1)


def set_time(timestamp: datetime, new_time: str):
    new_time = parse_time(new_time)
    return timestamp.replace(
        hour=new_time.hour,
        minute=new_time.minute,
        second=new_time.second,
        microsecond=new_time.microsecond,
    )


class ModelTests(TestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()
        self.monday_datetime = make_aware(parse_datetime("2019-11-25 00:00"))

        self.timeslot1 = Timeslot.objects.create(user=self.user1, name="Test")
        self.recurrence1 = TimeRecurrence.objects.create(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.MONDAY},
            start=parse_time("00:30:00"),
            end=parse_time("00:30:01"),
        )
        self.recurrence2 = TimeRecurrence.objects.create(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.MONDAY},
            start=parse_time("00:30:03"),
            end=parse_time("00:31"),
        )
        self.recurrence_all_day = TimeRecurrence.objects.create(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.TUESDAY},
            start=TimeRecurrence.DAY_START,
            end=TimeRecurrence.DAY_END,
        )

    def teardown(self):
        connect_signals()

    def test_time_recurrence(self):
        # Test set_time() helper function
        self.assertEqual(parse_datetime("2000-01-01 10:00"), set_time(parse_datetime("2000-01-01 00:00"), "10:00"))
        self.assertEqual(self.monday_datetime.strftime("%A"), "Monday")
        self.assertFalse(self.recurrence1.timestamp_is_within(set_time(self.monday_datetime, "00:29:01")))
        self.assertTrue(self.recurrence1.timestamp_is_within(set_time(self.monday_datetime, "00:30:00")))
        self.assertTrue(self.recurrence1.timestamp_is_within(set_time(self.monday_datetime, "00:30:01")))
        self.assertFalse(self.recurrence1.timestamp_is_within(set_time(self.monday_datetime, "00:30:02")))

    def test_timeslot(self):
        self.assertTrue(self.timeslot1.timestamp_is_within_time_recurrences(set_time(self.monday_datetime, "00:30:01")))
        self.assertFalse(
            self.timeslot1.timestamp_is_within_time_recurrences(set_time(self.monday_datetime, "00:30:02"))
        )
        self.assertTrue(self.timeslot1.timestamp_is_within_time_recurrences(set_time(self.monday_datetime, "00:30:03")))

    def test_source_fits(self):
        filter0 = Filter.objects.create(
            user=self.user1,
            name="Filter no source",
            filter_string='{"sourceSystemIds": []}',
        )
        filter1 = Filter.objects.create(
            user=self.user1,
            name="Filter1",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        filter2 = Filter.objects.create(
            user=self.user1,
            name="Filter2",
            filter_string=f'{{"sourceSystemIds": [{self.source2.pk}]}}',
        )

        self.assertEqual(filter0.tags_fit(self.incident1), None)
        self.assertTrue(filter1.source_system_fits(self.incident1))
        self.assertFalse(filter2.source_system_fits(self.incident1))

    def test_tags_fit(self):
        filter0 = Filter.objects.create(user=self.user1, name="Filter no tags", filter_string='{"tags": []}')
        filter1 = Filter.objects.create(user=self.user1, name="Filter1", filter_string=f'{{"tags": ["{self.tag1}"]}}')
        filter2 = Filter.objects.create(user=self.user1, name="Filter2", filter_string=f'{{"tags": ["{self.tag2}"]}}')

        self.assertEqual(filter0.tags_fit(self.incident1), None)
        self.assertTrue(filter1.tags_fit(self.incident1))
        self.assertFalse(filter2.tags_fit(self.incident1))

    def test_incident_fits(self):
        filter0 = Filter.objects.create(
            user=self.user1,
            name="Filter empty",
            filter_string='{"sourceSystemIds": [], "tags": []}',
        )
        self.assertFalse(filter0.incident_fits(self.incident1))
        filter1 = Filter.objects.create(
            user=self.user1,
            name="Filter1",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.assertTrue(filter1.incident_fits(self.incident1))
        self.assertFalse(filter1.incident_fits(self.incident2))
        filter3 = Filter.objects.create(user=self.user1, name="Filter3", filter_string=f'{{"tags": ["{self.tag1}"]}}')
        self.assertTrue(filter3.incident_fits(self.incident1))
        self.assertFalse(filter3.incident_fits(self.incident2))
        filter4 = Filter.objects.create(
            user=self.user1,
            name="Filter4",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}], "tags": ["{self.tag1}"]}}',
        )
        self.assertTrue(filter4.incident_fits(self.incident1))
        self.assertFalse(filter4.incident_fits(self.incident2))

    def test_filtered_incidents(self):
        filter0 = Filter.objects.create(
            user=self.user1,
            name="Filter empty",
            filter_string='{"sourceSystemIds": [], "tags": []}',
        )
        self.assertEqual(set(filter0.filtered_incidents), set())
        filter1 = Filter.objects.create(
            user=self.user1,
            name="Filter1",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.assertEqual(set(filter1.filtered_incidents), {self.incident1})
        filter2 = Filter.objects.create(
            user=self.user1,
            name="Filter2",
            filter_string=f'{{"sourceSystemIds": [{self.source2.pk}]}}',
        )
        self.assertEqual(set(filter2.filtered_incidents), {self.incident2})
        filter3 = Filter.objects.create(user=self.user1, name="Filter3", filter_string=f'{{"tags": ["{self.tag1}"]}}')
        self.assertEqual(set(filter1.filtered_incidents), {self.incident1})
        filter4 = Filter.objects.create(
            user=self.user1,
            name="Filter4",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}], "tags": ["{self.tag1}"]}}',
        )
        self.assertEqual(set(filter1.filtered_incidents), {self.incident1})


class ViewTests(APITestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()

        incident1_json = IncidentSerializer([self.incident1], many=True).data
        self.incident1_json = JSONRenderer().render(incident1_json)

        self.timeslot1 = Timeslot.objects.create(user=self.user1, name="Never")
        self.timeslot2 = Timeslot.objects.create(user=self.user1, name="Never 2: Ever-expanding Void")
        filter1 = Filter.objects.create(
            user=self.user1,
            name="Critical incidents",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.notification_profile1 = NotificationProfile.objects.create(user=self.user1, timeslot=self.timeslot1)
        self.notification_profile1.filters.add(filter1)

    def teardown(self):
        connect_signals()

    def test_incidents_filtered_by_notification_profile_view(self):
        response = self.user1_rest_client.get(
            reverse("notification-profile:notification-profile-incidents", args=[self.notification_profile1.pk])
        )
        response.render()
        self.assertEqual(response.content, self.incident1_json)

    def test_notification_profile_can_properly_change_timeslot(self):
        profile1_pk = self.notification_profile1.pk
        profile1_path = reverse("notification-profile:notification-profile", args=[profile1_pk])

        self.assertEqual(self.user1.notification_profiles.get(pk=profile1_pk).timeslot, self.timeslot1)
        self.assertEqual(self.user1_rest_client.get(profile1_path).status_code, status.HTTP_200_OK)
        response = self.user1_rest_client.put(
            profile1_path,
            {
                "timeslot": self.timeslot2.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "media": self.notification_profile1.media,
                "phone_number": self.notification_profile1.phone_number_id,
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_profile1_pk = response.data["pk"]

        self.assertEqual(self.user1_rest_client.get(profile1_path).status_code, status.HTTP_404_NOT_FOUND)
        with self.assertRaises(NotificationProfile.DoesNotExist):
            self.notification_profile1.refresh_from_db()
        self.assertTrue(self.user1.notification_profiles.filter(pk=new_profile1_pk).exists())
        self.assertEqual(self.user1.notification_profiles.get(pk=new_profile1_pk).timeslot, self.timeslot2)
        new_profile1_path = reverse("notification-profile:notification-profile", args=[new_profile1_pk])
        self.assertEqual(self.user1_rest_client.get(new_profile1_path).status_code, status.HTTP_200_OK)

    # TODO: test more endpoints
