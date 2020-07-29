from datetime import datetime, time

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase

from argus.auth.models import User
from argus.incident.models import (
    Incident,
    Object,
    ObjectType,
    ProblemType,
    SourceSystem,
    SourceSystemType,
)
from argus.incident.serializers import IncidentSerializer
from argus.notificationprofile.models import (
    Filter,
    NotificationProfile,
    TimeRecurrence,
    Timeslot,
)


class MockIncidentData:
    # Define member variables, to avoid warnings
    user = None
    nav1 = None
    zabbix1 = None
    object_type1 = None
    object1 = None
    problem_type1 = None
    incident1 = None
    incident2 = None

    def init_mock_data(self):
        self.user = User.objects.create(username="asdf")

        nav_type = SourceSystemType.objects.create(name="NAV")
        zabbix_type = SourceSystemType.objects.create(name="Zabbix")

        self.nav1 = SourceSystem.objects.create(
            name="Gløshaugen", type=nav_type, user=User.objects.create(username="nav.glos.no"),
        )
        self.zabbix1 = SourceSystem.objects.create(
            name="Gløshaugen", type=zabbix_type, user=User.objects.create(username="zabbix.glos.no"),
        )

        self.object_type1 = ObjectType.objects.create(name="box")
        self.object1 = Object.objects.create(name="1", url="", type=self.object_type1)

        self.problem_type1 = ProblemType.objects.create(name="boxDown", description="A box is down.")

        self.incident1 = Incident.objects.create(
            timestamp=timezone.now(),
            source=self.nav1,
            source_incident_id="123",
            object=self.object1,
            problem_type=self.problem_type1,
        )
        self.incident2 = Incident.objects.get(pk=self.incident1.pk)
        self.incident2.pk = None  # clones incident1
        self.incident2.source = self.zabbix1
        self.incident2.save()


class ModelTests(TestCase, MockIncidentData):
    @staticmethod
    def replace_time(timestamp: datetime, new_time: str):
        new_time = time.fromisoformat(new_time)
        return timestamp.replace(
            hour=new_time.hour, minute=new_time.minute, second=new_time.second, microsecond=new_time.microsecond,
        )

    def setUp(self):
        super().init_mock_data()
        self.monday_time = make_aware(datetime.fromisoformat("2019-11-25"))

        self.timeslot1 = Timeslot.objects.create(user=self.user, name="Test")
        self.recurrence1 = TimeRecurrence.objects.create(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.MONDAY},
            start=time.fromisoformat("00:30:00"),
            end=time.fromisoformat("00:30:01"),
        )
        self.recurrence2 = TimeRecurrence.objects.create(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.MONDAY},
            start=time.fromisoformat("00:30:03"),
            end=time.fromisoformat("00:31"),
        )
        self.recurrence_all_day = TimeRecurrence.objects.create(
            timeslot=self.timeslot1,
            days={TimeRecurrence.Day.TUESDAY},
            start=TimeRecurrence.DAY_START,
            end=TimeRecurrence.DAY_END,
        )

    def test_time_recurrence(self):
        # Test replace_time() helper function
        self.assertEqual(
            datetime.fromisoformat("2000-01-01 10:00"),
            self.replace_time(datetime.fromisoformat("2000-01-01"), "10:00"),
        )

        self.assertEqual(self.monday_time.strftime("%A"), "Monday")

        self.assertFalse(self.recurrence1.timestamp_is_within(self.replace_time(self.monday_time, "00:29:01")))
        self.assertTrue(self.recurrence1.timestamp_is_within(self.replace_time(self.monday_time, "00:30:00")))
        self.assertTrue(self.recurrence1.timestamp_is_within(self.replace_time(self.monday_time, "00:30:01")))
        self.assertFalse(self.recurrence1.timestamp_is_within(self.replace_time(self.monday_time, "00:30:02")))

    def test_timeslot(self):
        self.assertTrue(
            self.timeslot1.timestamp_is_within_time_recurrences(self.replace_time(self.monday_time, "00:30:01"))
        )
        self.assertFalse(
            self.timeslot1.timestamp_is_within_time_recurrences(self.replace_time(self.monday_time, "00:30:02"))
        )
        self.assertTrue(
            self.timeslot1.timestamp_is_within_time_recurrences(self.replace_time(self.monday_time, "00:30:03"))
        )

    def test_filter(self):
        filter1 = Filter.objects.create(
            user=self.user,
            name="Filter1",
            filter_string="{"
            f'"sourceSystemIds":[{self.nav1.pk}], "objectTypeIds":[], "parentObjectIds":[], "problemTypeIds":[]'
            "}",
        )
        filter2 = Filter.objects.create(
            user=self.user,
            name="Filter2",
            filter_string="{"
            f'"sourceSystemIds":[{self.zabbix1.pk}], "objectTypeIds":[], "parentObjectIds":[], "problemTypeIds":[]'
            "}",
        )

        self.assertTrue(filter1.incident_fits(self.incident1))
        self.assertFalse(filter1.incident_fits(self.incident2))

        self.assertFalse(filter2.incident_fits(self.incident1))
        self.assertTrue(filter2.incident_fits(self.incident2))

        self.assertEqual(set(filter1.filtered_incidents), {self.incident1})
        self.assertEqual(set(filter2.filtered_incidents), {self.incident2})


class ViewTests(APITestCase, MockIncidentData):
    def setUp(self):
        super().init_mock_data()

        user_token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + user_token.key)

        incident1_json = IncidentSerializer([self.incident1], many=True).data
        self.incident1_json = JSONRenderer().render(incident1_json)

        timeslot1 = Timeslot.objects.create(user=self.user, name="Never")
        filter1 = Filter.objects.create(
            user=self.user,
            name="Critical incidents",
            filter_string="{"
            f'"sourceSystemIds":[{self.nav1.pk}], "objectTypeIds":[], "parentObjectIds":[], "problemTypeIds":[]'
            "}",
        )
        self.notification_profile1 = NotificationProfile.objects.create(user=self.user, timeslot=timeslot1)
        self.notification_profile1.filters.add(filter1)

    def test_incidents_filtered_by_notification_profile_view(self):
        response = self.client.get(
            reverse("notification-profile:notification-profile-incidents", args=[self.notification_profile1.pk])
        )
        response.render()
        self.assertEqual(response.content, self.incident1_json)

    # TODO: test more endpoints
