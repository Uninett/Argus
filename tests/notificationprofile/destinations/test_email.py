from django.test import TestCase, tag
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from argus.auth.factories import PersonUserFactory
from argus.incident.factories import EventFactory, IncidentFactory
from argus.notificationprofile.factories import DestinationConfigFactory, NotificationProfileFactory, TimeslotFactory
from argus.notificationprofile.media.email import EmailNotification
from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.v2.serializers import RequestDestinationConfigSerializer
from argus.util.testing import connect_signals, disconnect_signals


@tag("integration")
class EmailDestinationConfigSerializerV2Tests(TestCase):
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
            {"email_address": "user@example.com"},
        )

    def test_can_create_email_destination(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "email",
            "settings": {
                "email_address": "user@example.com",
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
            },
        )

    def test_can_update_email_destination(self):
        destination = DestinationConfigFactory(
            user=self.user,
            media_id="email",
            settings={
                "email_address": "user@example.com",
            },
        )

        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "email",
            "settings": {
                "email_address": "new.email@example.com",
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

    def tearDown(self):
        connect_signals()

    def test_default_email_destination_should_be_created_if_user_has_email(self):
        # PersonUserFactory creates user with email address
        default_destination = self.user1.destinations.first()
        self.assertTrue(default_destination)
        self.assertTrue(default_destination.managed)

    def test_default_email_destination_should_not_be_created_if_user_has_no_email(self):
        self.assertFalse(self.user2.destinations.filter(media_id="email", managed=True).exists())

    def test_default_email_destination_should_be_added_if_email_is_added_to_user(self):
        self.user2.email = self.user2.username
        self.user2.save(update_fields=["email"])
        default_destination = self.user2.destinations.first()
        self.assertTrue(default_destination)
        self.assertTrue(default_destination.managed)

    def test_default_email_destination_should_be_updated_if_user_email_changes(self):
        self.user2.email = "new.email@example.com"
        self.user2.save(update_fields=["email"])
        default_destination = self.user2.destinations.filter(managed=True).first()
        self.assertEqual(self.user2.email, default_destination.settings["email_address"])

    def test_default_email_destination_should_be_deleted_if_user_email_is_deleted(self):
        self.user1.email = ""
        self.user1.save(update_fields=["email"])
        self.assertFalse(self.user1.destinations.filter(managed=True))


@tag("API", "integration")
class EmailMediumViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=user1)

    def tearDown(self):
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

        response = self.user1_rest_client.get(path="/api/v2/notificationprofiles/media/email/json_schema/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data, schema)

    def test_should_get_email_medium(self):
        response = self.user1_rest_client.get(path="/api/v2/notificationprofiles/media/email/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["name"], "Email")


@tag("API", "integration")
class EmailDestinationViewV2Tests(APITestCase):
    ENDPOINT = "/api/v2/notificationprofiles/destinations/"

    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        timeslot1 = TimeslotFactory(user=self.user1, name="Never")

        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=timeslot1)
        # Default email destination is automatically created with user
        self.managed_email_destination = self.user1.destinations.get()
        self.unmanaged_email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={"email_address": "test@example.com"},
            managed=False,
        )
        self.notification_profile1.destinations.set([self.managed_email_destination])

    def tearDown(self):
        connect_signals()

    def test_when_getting_list_of_destinations_then_return_destinations(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        response_pks = [destination["pk"] for destination in response.data]
        self.assertIn(self.unmanaged_email_destination.pk, response_pks)
        self.assertIn(self.managed_email_destination.pk, response_pks)

    def test_when_getting_managed_destination_then_return_destination(self):
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.managed_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["pk"], self.managed_email_destination.pk)
        self.assertEqual(response.data["media"]["slug"], self.managed_email_destination.media.slug)
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": self.managed_email_destination.settings["email_address"],
                "synced": self.managed_email_destination.managed,
            },
        )

    def test_when_getting_unmanaged_destination_then_return_destination(self):
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["pk"], self.unmanaged_email_destination.pk)
        self.assertEqual(response.data["media"]["slug"], self.unmanaged_email_destination.media.slug)
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": self.unmanaged_email_destination.settings["email_address"],
                "synced": self.unmanaged_email_destination.managed,
            },
        )

    def test_given_unmanaged_unused_destination_then_delete_destination(self):
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertFalse(DestinationConfig.objects.filter(id=self.unmanaged_email_destination.pk).exists())

    def test_given_managed_destination_then_forbid_deleting_destination(self):
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.managed_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("Cannot delete this destination since it was defined by an outside source", str(response.data))
        self.assertTrue(DestinationConfig.objects.filter(id=self.managed_email_destination.pk).exists())

    def test_given_destination_in_use_then_forbid_deleting_destination(self):
        self.notification_profile1.destinations.add(self.unmanaged_email_destination)
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn(
            "Cannot delete this destination since it is in use in the notification profile(s)", str(response.data)
        )
        self.assertTrue(DestinationConfig.objects.filter(id=self.unmanaged_email_destination.pk).exists())

    def test_given_valid_values_then_create_destination(self):
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
        self.assertEqual(response.data["media"]["slug"], "email")
        self.assertEqual(response.data["settings"], {"email_address": "test2@example.com", "synced": False})
        self.assertTrue(
            DestinationConfig.objects.filter(
                settings={"email_address": "test2@example.com"},
                managed=False,
            ).exists()
        )

    def test_given_valid_label_then_create_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "label": "new email",
                "settings": {
                    "email_address": "test2@example.com",
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["label"], "new email")
        self.assertTrue(DestinationConfig.objects.filter(label="new email").exists())

    def test_given_duplicate_label_then_forbid_creating_destination(self):
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            label="duplicate",
            settings={"email_address": "a@example.com"},
        )
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "label": "duplicate",
                "settings": {"email_address": "b@example.com"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A destination with this medium and label already exists", str(response.data))
        self.assertEqual(
            DestinationConfig.objects.filter(media_id="email", label="duplicate").count(),
            1,
        )

    def test_given_duplicate_email_address_then_forbid_creating_destination(self):
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
        self.assertIn("A destination with these settings already exists", str(response.data))
        self.assertEqual(
            DestinationConfig.objects.filter(
                media_id="email", settings__email_address=settings["email_address"]
            ).count(),
            1,
        )

    def test_given_settings_not_a_dict_then_forbid_creating_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "settings": "not a dict",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid JSON", str(response.data["settings"]))

    def test_given_invalid_email_address_then_forbid_creating_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "settings": {"email_address": "invalid"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid email address", str(response.data["email_address"]))

    def test_given_missing_email_address_then_forbid_creating_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "settings": {"other": "setting"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required", str(response.data["email_address"]))

    def test_given_empty_settings_then_forbid_creating_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "settings": {},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required", str(response.data["email_address"]))

    def test_given_same_medium_and_settings_to_update_unmanaged_destination_then_it_should_update(self):
        new_settings = {
            "email_address": "test2@example.com",
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={
                "media": self.unmanaged_email_destination.media.slug,
                "settings": new_settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["media"]["slug"], self.unmanaged_email_destination.media.slug)
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": new_settings["email_address"],
                "synced": self.unmanaged_email_destination.managed,
            },
        )
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"],
            new_settings["email_address"],
        )

    def test_given_settings_to_update_unmanaged_destination_then_it_should_update(self):
        new_settings = {
            "email_address": "test2@example.com",
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={
                "settings": new_settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["media"]["slug"], self.unmanaged_email_destination.media.slug)
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": new_settings["email_address"],
                "synced": self.unmanaged_email_destination.managed,
            },
        )
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"],
            new_settings["email_address"],
        )

    def test_given_label_to_update_managed_destination_then_it_should_update(self):
        data = {"label": "new_label"}
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.managed_email_destination.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["label"], data["label"])
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": self.managed_email_destination.settings["email_address"],
                "synced": self.managed_email_destination.managed,
            },
        )
        self.managed_email_destination.refresh_from_db()
        self.assertEqual(
            self.managed_email_destination.label,
            data["label"],
        )
        # Managed email destination is not copied
        self.assertTrue(self.managed_email_destination.managed)

    def test_given_label_to_update_unmanaged_destination_then_it_should_update(self):
        data = {"label": "new_label"}
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["label"], data["label"])
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": self.unmanaged_email_destination.settings["email_address"],
                "synced": self.unmanaged_email_destination.managed,
            },
        )
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.label,
            data["label"],
        )

    def test_given_label_and_settings_to_update_unmanaged_destination_then_it_should_update(self):
        data = {
            "label": "new_label",
            "settings": {"email_address": "test3@example.com"},
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["label"], data["label"])
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": data["settings"]["email_address"],
                "synced": self.unmanaged_email_destination.managed,
            },
        )
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.label,
            data["label"],
        )
        self.assertEqual(self.unmanaged_email_destination.settings, data["settings"])

    def test_given_settings_to_update_managed_destination_then_it_should_update_and_create_copy_of_old_settings(
        self,
    ):
        old_settings = self.managed_email_destination.settings.copy()
        new_settings = {
            "email_address": "test2@example.com",
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.managed_email_destination.pk}/",
            data={"settings": new_settings},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["pk"], self.managed_email_destination.pk)
        self.assertEqual(response.data["settings"], {"email_address": new_settings["email_address"], "synced": False})
        self.managed_email_destination.refresh_from_db()
        self.assertEqual(self.managed_email_destination.settings, new_settings)
        self.assertFalse(self.managed_email_destination.managed)
        self.assertTrue(DestinationConfig.objects.filter(managed=True, settings=old_settings).exists())

    def test_given_duplicate_label_then_forbid_updating_destination(self):
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            label="duplicate",
            settings={"email_address": "a@example.com"},
        )
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={"label": "duplicate"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A destination with this medium and label already exists", str(response.data))
        self.assertEqual(
            DestinationConfig.objects.filter(media_id="email", label="duplicate").count(),
            1,
        )

    def test_given_settings_not_dict_then_forbid_updating_destination(self):
        unmanaged_email_destination_address = self.unmanaged_email_destination.settings["email_address"]
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={"settings": "not a dict"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid JSON", str(response.data["settings"]))
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"], unmanaged_email_destination_address
        )

    def test_given_duplicate_email_address_then_forbid_updating_destination(self):
        settings = {"email_address": "test2@example.com"}
        email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings=settings,
        )
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{email_destination.pk}/",
            data={"settings": {"email_address": self.unmanaged_email_destination.settings["email_address"]}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        email_destination.refresh_from_db()
        self.assertEqual(email_destination.settings["email_address"], settings["email_address"])

    def test_given_invalid_email_address_then_forbid_updating_destination(self):
        unmanaged_email_destination_address = self.unmanaged_email_destination.settings["email_address"]
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={"settings": {"email_address": "invalid"}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid email address", str(response.data["email_address"]))
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"], unmanaged_email_destination_address
        )

    def test_given_empty_settings_then_forbid_updating_destination(self):
        unmanaged_email_destination_address = self.unmanaged_email_destination.settings["email_address"]
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={"settings": {}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required", str(response.data["email_address"]))
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"], unmanaged_email_destination_address
        )


@tag("API", "integration")
class EmailDestinationViewV3Tests(APITestCase):
    ENDPOINT = "/api/v3/notificationprofiles/destinations/"

    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        timeslot1 = TimeslotFactory(user=self.user1, name="Never")

        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=timeslot1)
        # Default email destination is automatically created with user
        self.managed_email_destination = self.user1.destinations.get()
        self.unmanaged_email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={"email_address": "test@example.com"},
            managed=False,
        )
        self.notification_profile1.destinations.set([self.managed_email_destination])

    def tearDown(self):
        connect_signals()

    def test_when_getting_list_of_destinations_then_return_destinations(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        response_pks = [destination["pk"] for destination in response.data]
        self.assertIn(self.unmanaged_email_destination.pk, response_pks)
        self.assertIn(self.managed_email_destination.pk, response_pks)

    def test_when_getting_managed_destination_then_return_destination(self):
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.managed_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["pk"], self.managed_email_destination.pk)
        self.assertEqual(response.data["media"]["slug"], self.managed_email_destination.media.slug)
        self.assertEqual(response.data["managed"], True)
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": self.managed_email_destination.settings["email_address"],
            },
        )

    def test_when_getting_unmanaged_destination_then_return_destination(self):
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["pk"], self.unmanaged_email_destination.pk)
        self.assertEqual(response.data["media"]["slug"], self.unmanaged_email_destination.media.slug)
        self.assertEqual(response.data["managed"], False)
        self.assertEqual(
            response.data["settings"],
            {
                "email_address": self.unmanaged_email_destination.settings["email_address"],
            },
        )

    def test_given_unmanaged_unused_destination_then_delete_destination(self):
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertFalse(DestinationConfig.objects.filter(id=self.unmanaged_email_destination.pk).exists())

    def test_given_managed_destination_then_forbid_deleting_destination(self):
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.managed_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("Cannot delete this destination since it was defined by an outside source", str(response.data))
        self.assertTrue(DestinationConfig.objects.filter(id=self.managed_email_destination.pk).exists())

    def test_given_destination_in_use_then_forbid_deleting_destination(self):
        self.notification_profile1.destinations.add(self.unmanaged_email_destination)
        response = self.user1_rest_client.delete(path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn(
            "Cannot delete this destination since it is in use in the notification profile(s)", str(response.data)
        )
        self.assertTrue(DestinationConfig.objects.filter(id=self.unmanaged_email_destination.pk).exists())

    def test_given_valid_values_then_create_destination(self):
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
        self.assertEqual(response.data["media"]["slug"], "email")
        self.assertEqual(response.data["managed"], None)
        self.assertEqual(response.data["settings"], {"email_address": "test2@example.com"})
        self.assertTrue(
            DestinationConfig.objects.filter(
                settings={"email_address": "test2@example.com"},
                managed=None,
            ).exists()
        )

    def test_given_valid_label_then_create_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "label": "new email",
                "settings": {
                    "email_address": "test2@example.com",
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["label"], "new email")
        self.assertTrue(DestinationConfig.objects.filter(label="new email").exists())

    def test_given_duplicate_label_then_forbid_creating_destination(self):
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            label="duplicate",
            settings={"email_address": "a@example.com"},
        )
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "label": "duplicate",
                "settings": {"email_address": "b@example.com"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A destination with this medium and label already exists", str(response.data))
        self.assertEqual(
            DestinationConfig.objects.filter(media_id="email", label="duplicate").count(),
            1,
        )

    def test_given_duplicate_email_address_then_forbid_creating_destination(self):
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
        self.assertIn("A destination with these settings already exists", str(response.data))
        self.assertEqual(
            DestinationConfig.objects.filter(
                media_id="email", settings__email_address=settings["email_address"]
            ).count(),
            1,
        )

    def test_given_settings_not_a_dict_then_forbid_creating_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "settings": "not a dict",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid JSON", str(response.data["settings"]))

    def test_given_invalid_email_address_then_forbid_creating_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "settings": {"email_address": "invalid"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid email address", str(response.data["email_address"]))

    def test_given_missing_email_address_then_forbid_creating_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "settings": {"other": "setting"},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required", str(response.data["email_address"]))

    def test_given_empty_settings_then_forbid_creating_destination(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "email",
                "settings": {},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required", str(response.data["email_address"]))

    def test_given_same_medium_and_settings_to_update_unmanaged_destination_then_it_should_update(self):
        new_settings = {
            "email_address": "test2@example.com",
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={
                "media": self.unmanaged_email_destination.media.slug,
                "settings": new_settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["media"]["slug"], self.unmanaged_email_destination.media.slug)
        self.assertEqual(response.data["managed"], False)
        self.assertEqual(
            response.data["settings"],
            {"email_address": new_settings["email_address"]},
        )
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"],
            new_settings["email_address"],
        )

    def test_given_settings_to_update_unmanaged_destination_then_it_should_update(self):
        email_destination = self.unmanaged_email_destination
        new_settings = {
            "email_address": "test2@example.com",
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{email_destination.pk}/",
            data={
                "settings": new_settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        email_destination.refresh_from_db()
        self.assertEqual(
            email_destination.settings["email_address"],
            new_settings["email_address"],
        )

    def test_given_label_to_update_managed_destination_then_it_should_update(self):
        data = {"label": "new_label"}
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.managed_email_destination.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["label"], data["label"])
        self.assertEqual(response.data["managed"], True)
        self.assertEqual(
            response.data["settings"],
            {"email_address": self.managed_email_destination.settings["email_address"]},
        )
        self.managed_email_destination.refresh_from_db()
        self.assertEqual(
            self.managed_email_destination.label,
            data["label"],
        )
        # Managed email destination is not copied
        self.assertTrue(self.managed_email_destination.managed)

    def test_given_label_to_update_unmanaged_destination_then_it_should_update(self):
        data = {"label": "new_label"}
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["label"], data["label"])
        self.assertEqual(response.data["managed"], False)
        self.assertEqual(
            response.data["settings"],
            {"email_address": self.unmanaged_email_destination.settings["email_address"]},
        )
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.label,
            data["label"],
        )

    def test_given_label_and_settings_to_update_unmanaged_destination_then_it_should_update(self):
        data = {
            "label": "new_label",
            "settings": {"email_address": "test3@example.com"},
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["label"], data["label"])
        self.assertEqual(response.data["managed"], False)
        self.assertEqual(
            response.data["settings"],
            {"email_address": data["settings"]["email_address"]},
        )
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.label,
            data["label"],
        )
        self.assertEqual(self.unmanaged_email_destination.settings, data["settings"])

    def test_given_settings_to_update_managed_destination_then_it_should_update_and_create_copy_of_old_settings(
        self,
    ):
        old_settings = self.managed_email_destination.settings.copy()
        new_settings = {
            "email_address": "test2@example.com",
        }
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.managed_email_destination.pk}/",
            data={"settings": new_settings},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["pk"], self.managed_email_destination.pk)
        self.assertEqual(response.data["managed"], False)
        self.assertEqual(response.data["settings"], {"email_address": new_settings["email_address"]})
        self.managed_email_destination.refresh_from_db()
        self.assertEqual(self.managed_email_destination.settings, new_settings)
        self.assertFalse(self.managed_email_destination.managed)
        self.assertTrue(DestinationConfig.objects.filter(managed=True, settings=old_settings).exists())

    def test_given_duplicate_label_then_forbid_updating_destination(self):
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            label="duplicate",
            settings={"email_address": "a@example.com"},
        )
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={"label": "duplicate"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A destination with this medium and label already exists", str(response.data))
        self.assertEqual(
            DestinationConfig.objects.filter(media_id="email", label="duplicate").count(),
            1,
        )

    def test_given_settings_not_dict_then_forbid_updating_destination(self):
        unmanaged_email_destination_address = self.unmanaged_email_destination.settings["email_address"]
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={"settings": "not a dict"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid JSON", str(response.data["settings"]))
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"], unmanaged_email_destination_address
        )

    def test_given_duplicate_email_address_then_forbid_updating_destination(self):
        settings = {"email_address": "test2@example.com"}
        email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings=settings,
        )
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{email_destination.pk}/",
            data={"settings": {"email_address": self.unmanaged_email_destination.settings["email_address"]}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        email_destination.refresh_from_db()
        self.assertEqual(email_destination.settings["email_address"], settings["email_address"])

    def test_given_invalid_email_address_then_forbid_updating_destination(self):
        unmanaged_email_destination_address = self.unmanaged_email_destination.settings["email_address"]
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={"settings": {"email_address": "invalid"}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid email address", str(response.data["email_address"]))
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"], unmanaged_email_destination_address
        )

    def test_given_empty_settings_then_forbid_updating_destination(self):
        unmanaged_email_destination_address = self.unmanaged_email_destination.settings["email_address"]
        response = self.user1_rest_client.patch(
            path=f"{self.ENDPOINT}{self.unmanaged_email_destination.pk}/",
            data={"settings": {}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required", str(response.data["email_address"]))
        self.unmanaged_email_destination.refresh_from_db()
        self.assertEqual(
            self.unmanaged_email_destination.settings["email_address"], unmanaged_email_destination_address
        )


@tag("integration")
class EmailDestinationSendTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

    def tearDown(self):
        connect_signals()

    def test_given_disabled_notifications_should_return_false(self):
        event = EventFactory(incident=IncidentFactory())
        destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={"email_address": "test@example.com"},
        )
        with self.settings(SEND_NOTIFICATIONS=False):
            self.assertFalse(EmailNotification.send(event, [destination]))

    def test_get_relevant_addresses_returns_only_email_addresses(self):
        email_address = "test2@example.com"
        email_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={"email_address": email_address},
            managed=False,
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
