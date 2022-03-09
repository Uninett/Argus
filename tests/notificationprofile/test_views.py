from django.urls import reverse
from django.test import tag

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase

from argus.incident.serializers import IncidentSerializer
from argus.notificationprofile.models import (
    Filter,
    NotificationProfile,
    Timeslot,
)
from argus.util.testing import disconnect_signals, connect_signals

from . import IncidentAPITestCaseHelper


@tag("API", "integration")
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
        self.notification_profile1.destinations.set(self.user1.destinations.all())

    def teardown(self):
        connect_signals()

    def test_incidents_filtered_by_notification_profile_view(self):
        response = self.user1_rest_client.get(
            reverse("v2:notification-profile:notificationprofile-incidents", args=[self.notification_profile1.pk])
        )
        response.render()
        self.assertEqual(response.content, self.incident1_json)

    def test_notification_profile_can_properly_change_timeslot(self):
        profile1_pk = self.notification_profile1.pk
        profile1_path = reverse("v2:notification-profile:notificationprofile-detail", args=[profile1_pk])

        self.assertEqual(self.user1.notification_profiles.get(pk=profile1_pk).timeslot, self.timeslot1)
        self.assertEqual(self.user1_rest_client.get(profile1_path).status_code, status.HTTP_200_OK)
        response = self.user1_rest_client.put(
            profile1_path,
            {
                "timeslot": self.timeslot2.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "active": self.notification_profile1.active,
                "destinations": [destination.pk for destination in self.notification_profile1.destinations.all()],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_profile1_pk = response.data["pk"]

        self.assertEqual(self.user1_rest_client.get(profile1_path).status_code, status.HTTP_404_NOT_FOUND)
        with self.assertRaises(NotificationProfile.DoesNotExist):
            self.notification_profile1.refresh_from_db()
        self.assertTrue(self.user1.notification_profiles.filter(pk=new_profile1_pk).exists())
        self.assertEqual(self.user1.notification_profiles.get(pk=new_profile1_pk).timeslot, self.timeslot2)
        new_profile1_path = reverse("v2:notification-profile:notificationprofile-detail", args=[new_profile1_pk])
        self.assertEqual(self.user1_rest_client.get(new_profile1_path).status_code, status.HTTP_200_OK)

    # TODO: test more endpoints
