from django.urls import reverse
from django.test import tag

from rest_framework import status
from rest_framework.test import APITestCase

from argus.notificationprofile.factories import (
    TimeslotFactory,
    FilterFactory,
    NotificationProfileFactory,
    DestinationConfigFactory,
)
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

    def test_notification_profile_can_update_timeslot_without_changing_pk(self):
        # Originally timeslot was the pk of notification profile
        profile1_pk = self.notification_profile1.pk
        profile1_path = f"/api/v2/notificationprofiles/{profile1_pk}/"

        response = self.user1_rest_client.put(
            path=profile1_path,
            data={
                "timeslot": self.timeslot2.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "destinations": [self.synced_email_destination.pk],
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], profile1_pk)
        self.assertEqual(NotificationProfile.objects.get(pk=profile1_pk).timeslot.pk, self.timeslot2.pk)

    def test_can_get_all_destinations(self):
        response = self.user1_rest_client.get(path="/api/v2/notificationprofiles/destinations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        response_settings = [destination["settings"] for destination in response.data]
        self.assertTrue(self.synced_email_destination.settings in response_settings)
        self.assertTrue(self.non_synced_email_destination.settings in response_settings)
        self.assertTrue(self.sms_destination.settings in response_settings)

    def test_can_get_destination(self):
        response = self.user1_rest_client.get(
            path=f"/api/v2/notificationprofiles/destinations/{self.synced_email_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["settings"], self.synced_email_destination.settings)

    def test_can_create_email_destination_with_valid_values(self):
        response = self.user1_rest_client.post(
            path="/api/v2/notificationprofiles/destinations/",
            data={
                "media": "email",
                "settings": {
                    "email_address": "test2@example.com",
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            DestinationConfig.objects.filter(
                settings={
                    "email_address": "test2@example.com",
                    "synced": False,
                },
            ).exists()
        )

    def test_cannot_create_email_destination_with_duplicate_email_address(self):
        settings = {"email_address": "test2@example.com"}
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings=settings,
        )
        response = self.user1_rest_client.post(
            path="/api/v2/notificationprofiles/destinations/",
            data={
                "media": "email",
                "settings": settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            DestinationConfig.objects.filter(
                media_id="email", settings__email_address=settings["email_address"]
            ).count(),
            1,
        )

    def test_can_create_sms_destination_with_valid_values(self):
        response = self.user1_rest_client.post(
            path="/api/v2/notificationprofiles/destinations/",
            data={
                "media": "sms",
                "settings": {
                    "phone_number": "+4747474740",
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            DestinationConfig.objects.filter(
                settings={
                    "phone_number": "+4747474740",
                },
            ).exists()
        )

    def test_cannot_create_sms_destination_with_duplicate_phone_number(self):
        settings = {"phone_number": "+4747474701"}
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings=settings,
        )
        response = self.user1_rest_client.post(
            path="/api/v2/notificationprofiles/destinations/",
            data={
                "media": "sms",
                "settings": settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DestinationConfig.objects.filter(media_id="sms", settings=settings).count(), 1)

    def test_can_update_email_destination_with_same_medium(self):
        email_destination = self.non_synced_email_destination
        new_settings = {
            "email_address": "test2@example.com",
        }
        response = self.user1_rest_client.patch(
            path=f"/api/v2/notificationprofiles/destinations/{email_destination.pk}/",
            data={
                "media": "email",
                "settings": new_settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        email_destination.refresh_from_db()
        self.assertEqual(
            email_destination.settings["email_address"],
            new_settings["email_address"],
        )

    def test_cannot_update_email_destination_with_duplicate_email_address(self):
        settings = {"email_address": "test2@example.com"}
        email_destination_pk = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings=settings,
        ).pk
        response = self.user1_rest_client.patch(
            path=f"/api/v2/notificationprofiles/destinations/{email_destination_pk}/",
            data={"settings": {"email_address": self.non_synced_email_destination.settings["email_address"]}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            DestinationConfig.objects.get(pk=email_destination_pk).settings["email_address"], settings["email_address"]
        )

    def test_can_update_sms_destination_with_same_medium(self):
        sms_destination = self.sms_destination
        new_settings = {
            "phone_number": "+4747474746",
        }
        response = self.user1_rest_client.patch(
            path=f"/api/v2/notificationprofiles/destinations/{sms_destination.pk}/",
            data={
                "media": "sms",
                "settings": new_settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sms_destination.refresh_from_db()
        self.assertEqual(
            sms_destination.settings,
            new_settings,
        )

    def test_cannot_update_sms_destination_with_duplicate_phone_number(self):
        settings1 = {"phone_number": "+4747474701"}
        settings2 = {"phone_number": "+4747474702"}
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings=settings1,
        )
        sms_destination_pk = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings=settings2,
        ).pk
        response = self.user1_rest_client.patch(
            path=f"/api/v2/notificationprofiles/destinations/{sms_destination_pk}/", data={"settings": settings1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DestinationConfig.objects.get(pk=sms_destination_pk).settings, settings2)

    def test_can_delete_sms_destination(self):
        response = self.user1_rest_client.delete(
            path=f"/api/v2/notificationprofiles/destinations/{self.sms_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DestinationConfig.objects.filter(id=self.sms_destination.pk).exists())

    def test_can_delete_unsynced_unconnected_email_destination(self):
        response = self.user1_rest_client.delete(
            path=f"/api/v2/notificationprofiles/destinations/{self.non_synced_email_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DestinationConfig.objects.filter(id=self.non_synced_email_destination.pk).exists())

    def test_cannot_delete_synced_email_destination(self):
        response = self.user1_rest_client.delete(
            path=f"/api/v2/notificationprofiles/destinations/{self.synced_email_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(DestinationConfig.objects.filter(id=self.synced_email_destination.pk).exists())

    def test_cannot_delete_connected_email_destination(self):
        self.notification_profile1.destinations.add(self.non_synced_email_destination)
        response = self.user1_rest_client.delete(
            path=f"/api/v2/notificationprofiles/destinations/{self.non_synced_email_destination.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(DestinationConfig.objects.filter(id=self.non_synced_email_destination.pk).exists())

    def test_can_get_all_media(self):
        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(set([medium["slug"] for medium in response.data]), set(["sms", "email"]))

    def test_can_get_medium(self):
        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/email/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Email")
        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/sms/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "SMS")

    def test_can_get_json_schema_of_medium(self):
        sms_schema = {
            "json_schema": {
                "title": "SMS Settings",
                "description": "Settings for a DestinationConfig using SMS.",
                "type": "object",
                "required": ["phone_number"],
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "title": "Phone number",
                        "description": "The phone number is validated and the country code needs to be given.",
                    }
                },
                "$id": "http://testserver/json-schema/sms",
            }
        }
        email_schema = {
            "json_schema": {
                "title": "Email Settings",
                "description": "Settings for a DestinationConfig using email.",
                "type": "object",
                "required": ["email_address"],
                "properties": {"email_address": {"type": "string", "title": "Email address"}},
                "$id": "http://testserver/json-schema/email",
            }
        }

        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/email/json_schema/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, email_schema)

        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/sms/json_schema/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, sms_schema)
