from django.test import TestCase, tag
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import DestinationConfigFactory, NotificationProfileFactory, TimeslotFactory
from argus.notificationprofile.media.email import EmailNotification
from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.serializers import RequestDestinationConfigSerializer
from argus.util.testing import connect_signals, disconnect_signals


@tag("integration")
class EmailDestinationConfigSerializerTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.request_factory = APIRequestFactory()

    def test_email_destination_serializer_is_valid_with_correct_input(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {
                "email_address": "user@example.com",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_email_destination_serializer_is_invalid_with_empty_settings(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_email_destination_serializer_is_invalid_with_missing_key(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {"phone_number": "+4747474747"},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_email_destination_serializer_is_invalid_with_invalid_email_address(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {"email_address": "hello"},
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
            "media": "email",
            "settings": {
                "email_address": "user@example.com",
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
                "email_address": "user@example.com",
                "synced": False,
            },
        )

    def test_can_create_email_destination(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "email",
            "settings": {
                "email_address": "user@example.com",
                "synced": False,
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
                "email_address": "user@example.com",
                "synced": False,
            },
        )

    def test_can_update_email_destination(self):
        destination = DestinationConfigFactory(
            user=self.user,
            media_id="email",
            settings={
                "email_address": "user@example.com",
                "synced": False,
            },
        )

        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "email",
            "settings": {
                "email_address": "new.email@example.com",
                "synced": False,
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.update(destination, validated_data)
        self.assertEqual(obj.settings["email_address"], "new.email@example.com")

    def test_email_destination_serializer_is_invalid_with_different_medium(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {
                "email_address": "user@example.com",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        serializer.is_valid()
        destination = serializer.save(user=self.user)
        data = {
            "media": "sms",
            "settings": {
                "phone_number": "+4747474747",
            },
        }
        second_serializer = RequestDestinationConfigSerializer(
            instance=destination,
            data=data,
            context={"request": request},
        )
        self.assertFalse(second_serializer.is_valid())
        self.assertTrue(second_serializer.errors)


@tag("integration")
class EmailSignalTests(APITestCase):
    def setUp(self):
        disconnect_signals()

        self.user1 = PersonUserFactory()
        self.user2 = PersonUserFactory(email="")

    def teardown(self):
        connect_signals()

    def test_default_email_destination_should_be_created_if_user_has_email(self):
        # PersonUserFactory creates user with email address
        default_destination = self.user1.destinations.first()
        self.assertTrue(default_destination)
        self.assertTrue(default_destination.settings["synced"])

    def test_default_email_destination_should_not_be_created_if_user_has_no_email(self):
        self.assertFalse(self.user2.destinations.filter(media_id="email", settings__synced=True).exists())

    def test_default_email_destination_should_be_added_if_email_is_added_to_user(self):
        self.user2.email = self.user2.username
        self.user2.save(update_fields=["email"])
        default_destination = self.user2.destinations.first()
        self.assertTrue(default_destination)
        self.assertTrue(default_destination.settings["synced"])

    def test_default_email_destination_should_be_updated_if_user_email_changes(self):
        self.user2.email = "new.email@example.com"
        self.user2.save(update_fields=["email"])
        default_destination = self.user2.destinations.filter(settings__synced=True).first()
        self.assertEqual(self.user2.email, default_destination.settings["email_address"])

    def test_default_email_destination_should_be_deleted_if_user_email_is_deleted(self):
        self.user1.email = ""
        self.user1.save(update_fields=["email"])
        self.assertFalse(self.user1.destinations.filter(settings__synced=True))


@tag("API", "integration")
class EmailMediumViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=user1)

    def teardown(self):
        connect_signals()

    def test_should_get_json_schema_for_email(self):
        schema = {
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
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data, schema)

    def test_should_get_email_medium(self):
        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/email/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["name"], "Email")


@tag("API", "integration")
class EmailDestinationViewTests(APITestCase):
    ENDPOINT = "/api/v2/notificationprofiles/destinations/"

    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        timeslot1 = TimeslotFactory(user=self.user1, name="Never")

        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=timeslot1)
        # Default email destination is automatically created with user
        self.synced_email_destination = self.user1.destinations.get()
        self.non_synced_email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={"email_address": "test@example.com", "synced": False},
        )
        self.notification_profile1.destinations.set([self.synced_email_destination])

    def teardown(self):
        connect_signals()

    def test_should_delete_unsynced_unused_email_destination(self):
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.non_synced_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertFalse(DestinationConfig.objects.filter(id=self.non_synced_email_destination.pk).exists())

    def test_should_not_allow_deletion_of_synced_email_destination(self):
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.synced_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertTrue(DestinationConfig.objects.filter(id=self.synced_email_destination.pk).exists())

    def test_should_not_allow_deletion_of_email_destination_in_use(self):
        self.notification_profile1.destinations.add(self.non_synced_email_destination)
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.non_synced_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertTrue(DestinationConfig.objects.filter(id=self.non_synced_email_destination.pk).exists())

    def test_should_create_email_destination_with_valid_values(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
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

    def test_should_not_allow_creating_email_destination_with_duplicate_email_address(self):
        settings = {"email_address": "test2@example.com"}
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings=settings,
        )
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
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

    def test_should_update_email_destination_with_same_medium(self):
        email_destination = self.non_synced_email_destination
        new_settings = {
            "email_address": "test2@example.com",
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{email_destination.pk}/",
            data={
                "media": "email",
                "settings": new_settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        email_destination.refresh_from_db()
        self.assertEqual(
            email_destination.settings["email_address"],
            new_settings["email_address"],
        )

    def test_should_not_allow_updating_email_destination_with_duplicate_email_address(self):
        settings = {"email_address": "test2@example.com"}
        email_destination_pk = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings=settings,
        ).pk
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{email_destination_pk}/",
            data={"settings": {"email_address": self.non_synced_email_destination.settings["email_address"]}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            DestinationConfig.objects.get(pk=email_destination_pk).settings["email_address"], settings["email_address"]
        )


@tag("integration")
class EmailDestinationSendTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

    def teardown(self):
        connect_signals()

    def test_get_relevant_addresses_returns_only_email_addresses(self):
        email_address = "test2@example.com"
        email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={
                "email_address": email_address,
                "synced": False,
            },
        )
        phone_number = "+4747474747"
        sms_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get_or_create(slug="sms")[0],
            settings={
                "phone_number": phone_number,
            },
        )

        email_addresses = EmailNotification.get_relevant_addresses(
            [
                email_destination,
                sms_destination,
            ]
        )

        self.assertIn(email_address, email_addresses)
        self.assertNotIn(phone_number, email_addresses)
