from django.test import TestCase, tag
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import DestinationConfigFactory, NotificationProfileFactory
from argus.notificationprofile.media.sms_as_email import SMSNotification
from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.serializers import RequestDestinationConfigSerializer
from argus.util.testing import connect_signals, disconnect_signals


@tag("integration")
class SMSDestinationConfigSerializerTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.request_factory = APIRequestFactory()

    def test_sms_destination_serializer_is_valid_with_correct_input(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {
                "phone_number": "+4747474747",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_sms_destination_serializer_is_invalid_with_empty_settings(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_sms_destination_serializer_is_invalid_with_missing_key(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {"email_address": "user@example.com"},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_email_destination_serializer_is_invalid_with_invalid_phone_number(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {"phone_number": "+474747"},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_email_destination_serializer_is_valid_with_additional_arguments(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {
                "phone_number": "+4747474747",
                "extra_key": "something",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["settings"],
            {
                "phone_number": "+4747474747",
            },
        )

    def test_can_create_sms_destination(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "sms",
            "settings": {
                "phone_number": "+4747474747",
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.create(validated_data)
        self.assertEqual(
            obj.settings,
            {
                "phone_number": "+4747474747",
            },
        )

    def test_can_update_sms_destination(self):
        destination = DestinationConfigFactory(
            user=self.user,
            media_id="sms",
            settings={"phone_number": "+4747474747"},
        )

        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "sms",
            "settings": {
                "phone_number": "+4711111111",
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.update(destination, validated_data)
        self.assertEqual(obj.settings["phone_number"], "+4711111111")

    def test_sms_destination_serializer_is_invalid_with_different_medium(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {
                "phone_number": "+4747474747",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        serializer.is_valid()
        destination = serializer.save(user=self.user)
        data = {
            "media": "email",
            "settings": {
                "email_address": "user@example.com",
            },
        }
        second_serializer = RequestDestinationConfigSerializer(
            instance=destination,
            data=data,
            context={"request": request},
        )
        self.assertFalse(second_serializer.is_valid())
        self.assertTrue(second_serializer.errors)


@tag("API", "integration")
class SMSMediumViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=user1)

    def teardown(self):
        connect_signals()

    def test_should_get_json_schema_for_sms(self):
        schema = {
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

        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/sms/json_schema/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data, schema)

    def test_should_get_sms_medium(self):
        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/sms/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["name"], "SMS")


@tag("API", "integration")
class SMSDestinationViewTests(APITestCase):
    ENDPOINT = "/api/v2/notificationprofiles/destinations/"

    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        self.sms_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474747"},
        )

    def teardown(self):
        connect_signals()

    def test_should_create_sms_destination_with_valid_values(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
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

    def test_should_not_allow_creating_sms_destination_with_duplicate_phone_number(self):
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

    def test_should_update_sms_destination_with_same_medium(self):
        sms_destination = self.sms_destination
        new_settings = {
            "phone_number": "+4747474746",
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{sms_destination.pk}/",
            data={
                "media": "sms",
                "settings": new_settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        sms_destination.refresh_from_db()
        self.assertEqual(
            sms_destination.settings,
            new_settings,
        )

    def test_should_not_allow_updating_sms_destination_with_duplicate_phone_number(self):
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

    def test_should_delete_unused_sms_destination(self):
        response = self.user1_rest_client.delete(
            path=f"{self.ENDPOINT}{self.sms_destination.pk}/",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertFalse(DestinationConfig.objects.filter(id=self.sms_destination.pk).exists())

    def test_should_not_allow_deletion_of_sms_destination_in_use(self):
        notification_profile = NotificationProfileFactory(user=self.user1)
        notification_profile.destinations.add(self.sms_destination)
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.sms_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertTrue(DestinationConfig.objects.filter(pk=self.sms_destination.pk).exists())


@tag("integration")
class SMSDestinationSendTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

    def teardown(self):
        connect_signals()

    def test_get_relevant_addresses_returns_only_phone_numbers(self):
        phone_number = "+4747474747"
        sms_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get_or_create(slug="sms")[0],
            settings={
                "phone_number": phone_number,
            },
        )
        email_address = "test2@example.com"
        email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={
                "email_address": email_address,
                "synced": False,
            },
        )

        phone_numbers = SMSNotification.get_relevant_addresses(
            [
                email_destination,
                sms_destination,
            ]
        )

        self.assertIn(phone_number, phone_numbers)
        self.assertNotIn(email_address, phone_numbers)
