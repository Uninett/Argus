from django.urls import reverse
from django.test import tag

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase

from argus.incident.serializers import IncidentSerializer
from argus.notificationprofile.factories import (
    TimeslotFactory,
    FilterFactory,
    NotificationProfileFactory,
    DestinationConfigFactory,
)
from argus.notificationprofile.media import MEDIA_CLASSES_DICT
from argus.notificationprofile.models import (
    DestinationConfig,
    Media,
    NotificationProfile,
)
from argus.util.testing import disconnect_signals, connect_signals

from . import IncidentAPITestCaseHelper


@tag("API", "integration")
class ViewTests(APITestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()

        self.timeslot1 = TimeslotFactory(user=self.user1, name="Never")
        self.timeslot2 = TimeslotFactory(user=self.user1, name="Never 2: Ever-expanding Void")
        filter1 = FilterFactory(
            user=self.user1,
            name="Critical incidents",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=self.timeslot1)
        self.notification_profile1.filters.add(filter1)
        # Default email destination is automatically created with user
        self.synced_email_destination = self.user1.destinations.get()
        self.non_synced_email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={"email_address": "test@example.com", "synced": False},
        )
        self.sms_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474747"},
        )
        self.notification_profile1.destinations.set([self.synced_email_destination])

    def teardown(self):
        connect_signals()

    def test_can_get_all_incidents_of_notification_profile(self):
        response = self.user1_rest_client.get(
            path=f"/api/v2/notificationprofiles/{self.notification_profile1.pk}/incidents/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], self.incident1.pk)

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

    def test_can_delete_sms_destination(self):
        self.assertTrue(DestinationConfig.objects.filter(media_id="sms").exists())
        response = self.user1_rest_client.delete(
            path=f"/api/v2/notificationprofiles/destinations/{self.sms_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DestinationConfig.objects.filter(media_id="sms").exists())

    def test_can_delete_unsynced_unconnected_email_destination(self):
        self.assertTrue(DestinationConfig.objects.filter(media_id="email").filter(settings__synced=False).exists())
        response = self.user1_rest_client.delete(
            path=f"/api/v2/notificationprofiles/destinations/{self.non_synced_email_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DestinationConfig.objects.filter(media_id="email").filter(settings__synced=False).exists())

    def test_cannot_delete_synced_email_destination(self):
        self.assertTrue(DestinationConfig.objects.filter(media_id="email").filter(settings__synced=True).exists())
        response = self.user1_rest_client.delete(
            path=f"/api/v2/notificationprofiles/destinations/{self.synced_email_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(DestinationConfig.objects.filter(media_id="email").filter(settings__synced=True).exists())

    def test_cannot_delete_connected_email_destination(self):
        self.notification_profile1.destinations.add(self.non_synced_email_destination)

        self.assertTrue(DestinationConfig.objects.filter(media_id="email").filter(settings__synced=False).exists())
        response = self.user1_rest_client.delete(
            path=f"/api/v2/notificationprofiles/destinations/{self.non_synced_email_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(DestinationConfig.objects.filter(media_id="email").filter(settings__synced=False).exists())

    # TODO: test more endpoints
