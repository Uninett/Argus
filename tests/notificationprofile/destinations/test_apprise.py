from unittest.mock import patch

from django.test import TestCase, tag
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from argus.auth.factories import PersonUserFactory
from argus.incident.factories import EventFactory, IncidentFactory
from argus.notificationprofile.factories import DestinationConfigFactory, NotificationProfileFactory, TimeslotFactory
from argus.notificationprofile.media.base import AppriseMedium
from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.serializers import RequestDestinationConfigSerializer
from argus.util.testing import connect_signals, disconnect_signals


@tag("integration")
class AppriseDestinationConfigSerializerTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.request_factory = APIRequestFactory()

    def test_apprise_medium_serializer_is_valid_with_correct_input(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "apprise",
            "settings": {
                "destination_url": "https://example.com/hook",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_apprise_destination_serializer_is_invalid_with_empty_settings(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "apprise",
            "settings": {},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_apprise_destination_serializer_is_invalid_with_missing_key(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "apprise",
            "settings": {"email_address": "user@example.com"},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_apprise_destination_serializer_is_invalid_with_invalid_url(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "apprise",
            "settings": {
                "destination_url": "not a url bla bla",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_apprise_destination_serializer_is_valid_with_additional_arguments(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "apprise",
            "settings": {
                "destination_url": "https://example.com/hook",
                "fake_key": "fake_something",
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
                "destination_url": "https://example.com/hook",
            },
        )

    def test_can_create_apprise_destination(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "apprise",
            "settings": {
                "destination_url": "https://example.com/hook",
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
                "destination_url": "https://example.com/hook",
            },
        )

    def test_can_update_apprise_destination(self):
        destination = DestinationConfigFactory(
            user=self.user,
            media=Media.objects.get(slug="apprise"),
            settings={"destination_url": "https://old.example.com/hook"},
        )
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "apprise",
            "settings": {
                "destination_url": "https://new.example.com/hook",
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.update(destination, validated_data)
        self.assertEqual(obj.settings["destination_url"], "https://new.example.com/hook")

    def test_apprise_destination_serializer_is_invalid_with_different_medium(self):
        request = self.request_factory.post("/")
        request.user = self.user

        serializer = RequestDestinationConfigSerializer(
            data={
                "media": "apprise",
                "settings": {
                    "destination_url": "https://example.com/hook",
                },
            },
            context={"request": request},
        )
        serializer.is_valid()
        destination = serializer.save(user=self.user)

        second_serializer = RequestDestinationConfigSerializer(
            instance=destination,
            data={
                "media": "email",
                "settings": {"email_address": "user@example.com"},
            },
            context={"request": request},
        )
        self.assertFalse(second_serializer.is_valid())
        self.assertTrue(second_serializer.errors)


@tag("API", "integration")
class AppriseDestinationViewTests(APITestCase):
    ENDPOINT = "/api/v2/notificationprofiles/destinations/"

    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        timeslot1 = TimeslotFactory(user=self.user1, name="Never")

        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=timeslot1)
        self.destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="apprise"),
            settings={"destination_url": "https://example.com/hook"},
        )
        self.notification_profile1.destinations.set([self.destination])

    def tearDown(self):
        connect_signals()

    def test_should_create_apprise_destination_with_valid_values(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "apprise",
                "settings": {
                    "destination_url": "https://example2.com/hook",
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            DestinationConfig.objects.filter(
                settings={
                    "destination_url": "https://example2.com/hook",
                },
            ).exists()
        )

    def test_should_not_allow_creating_apprise_destination_with_duplicate_urls(self):
        settings = {"destination_url": "https://example.com/hook"}
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="apprise"),
            settings=settings,
        )
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "media": "apprise",
                "settings": settings,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            DestinationConfig.objects.filter(
                media_id="apprise", settings__destination_url=settings["destination_url"]
            ).count(),
            1,
        )


@tag("integration")
class AppriseMediumBehaviorTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.user = PersonUserFactory()
        self.incident = IncidentFactory()
        self.event = EventFactory(incident=self.incident)
        self.destination = DestinationConfigFactory(
            user=self.user,
            media=Media.objects.get(slug="apprise"),
            settings={"destination_url": "https://example.com/hook"},
        )

    def tearDown(self):
        connect_signals()

    def test_send_no_destinations_returns_false(self):
        self.assertFalse(AppriseMedium.send(self.event, []))

    @patch("argus.notificationprofile.media.apprise.Apprise")
    def test_send_success_single_destination(self, mock_apprise):
        instance = mock_apprise.return_value
        instance.notify.return_value = True
        self.assertTrue(AppriseMedium.send(self.event, [self.destination]))
        instance.add.assert_called_once_with("https://example.com/hook")

    @patch("argus.notificationprofile.media.apprise.Apprise")
    def test_send_failure_returns_false(self, mock_apprise):
        instance = mock_apprise.return_value
        instance.notify.return_value = False

        self.assertFalse(AppriseMedium.send(self.event, [self.destination]))
        instance.add.assert_called_once_with("https://example.com/hook")
