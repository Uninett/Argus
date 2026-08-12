from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings, tag
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from argus.auth.factories import PersonUserFactory
from argus.incident.factories import EventFactory, IncidentFactory
from argus.notificationprofile.factories import DestinationConfigFactory, NotificationProfileFactory, TimeslotFactory
from argus.notificationprofile.media.base import AppriseMedium
from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.v2.serializers import RequestDestinationConfigSerializer
from argus.util.testing import connect_signals, disconnect_signals


# Destination configuration tests not involving Apprise itself


@tag("integration")
class AppriseDestinationConfigSerializerTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.request_factory = APIRequestFactory()

    def test_given_correct_input_apprise_medium_serializer_should_be_valid(self):
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

    def test_given_empty_settings_apprise_medium_serializer_should_not_be_valid(self):
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

    def tests_given_missing_key_apprise_destination_serializer_should_not_be_valid(self):
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

    def test_given_invalid_url_apprise_destination_serializer_should_not_be_valid(self):
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

    def test_given_additional_arguments_apprise_destination_serializer_should_be_valid(self):
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

    def test_given_valid_request_should_create_apprise_destination(self):
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

    def test_given_valid_request_should_update_apprise_destination(self):
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

    def test_given_different_medium_apprise_destination_serializer_should_not_be_valid(self):
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

    def test_given_valid_values_should_create_apprise_destination(self):
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

    def test_given_duplicate_urls_should_not_allow_creating_apprise_destination(self):
        settings = {"destination_url": "https://duplicate-example.com/hook"}
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


# Tests for mocked Apprise send()


@tag("integration")
@override_settings(SEND_NOTIFICATIONS=True)
class AppriseMediumMockedLibraryTests(TestCase):
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

    def test_given_no_destinations_should_return_false(self):
        self.assertFalse(AppriseMedium.send(self.event, []))

    @override_settings(SEND_NOTIFICATIONS=False)
    @patch("argus.notificationprofile.media.base.Apprise")
    def test_given_disabled_notifications_should_return_false(self, mock_apprise):
        self.assertFalse(AppriseMedium.send(self.event, [self.destination]))
        mock_apprise.assert_not_called()

    @patch("argus.notificationprofile.media.base.Apprise", None)
    def test_when_apprise_not_installed_should_return_false(self):
        self.assertFalse(AppriseMedium.send(self.event, [self.destination]))

    @patch("argus.notificationprofile.media.base.Apprise")
    def test_given_no_notify_type_notifier_should_be_called_without_notify_type(self, mock_apprise):
        mock_apprise.return_value.notify.return_value = True

        AppriseMedium.send(self.event, [self.destination])

        _, call_kwargs = mock_apprise.return_value.notify.call_args
        self.assertNotIn("notify_type", call_kwargs)

    @patch("argus.notificationprofile.media.base.Apprise")
    def test_given_notify_type_notifier_should_be_called_with_notify_type(self, mock_apprise):
        mock_apprise.return_value.notify.return_value = True

        AppriseMedium.send(self.event, [self.destination], notify_type="warning")

        _, call_kwargs = mock_apprise.return_value.notify.call_args
        self.assertEqual(call_kwargs["notify_type"], "warning")


# Tests using the real Apprise library, posting to a local webhook


class _CapturingRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.server.payloads.append(json.loads(self.rfile.read(length)))
        self.send_response(self.server.response_status)
        self.end_headers()

    def log_message(self, *args):
        pass


class LocalAppriseWebhook(ThreadingHTTPServer):
    def __init__(self, response_status=200):
        super().__init__(("127.0.0.1", 0), _CapturingRequestHandler)
        self.payloads = []
        self.response_status = response_status
        # Without a short poll interval shutdown() blocks for up to 0.5s per server
        threading.Thread(target=self.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def stop(self):
        self.shutdown()
        self.server_close()

    @property
    def url(self):
        host, port = self.server_address[:2]
        return f"json://{host}:{port}/hook"


@tag("integration")
@override_settings(SEND_NOTIFICATIONS=True)
class AppriseMediumRealLibraryTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.user = PersonUserFactory()
        self.incident = IncidentFactory()
        self.event = EventFactory(incident=self.incident)

    def tearDown(self):
        connect_signals()

    def _destination_for(self, url):
        return DestinationConfigFactory(
            user=self.user,
            media=Media.objects.get(slug="apprise"),
            settings={"destination_url": url},
        )

    def _webhook_destination(self, response_status=200):
        webhook = LocalAppriseWebhook(response_status)
        self.addCleanup(webhook.stop)
        return webhook, self._destination_for(webhook.url)

    def test_given_single_destination_should_post_notification_to_webhook(self):
        webhook, destination = self._webhook_destination()

        self.assertTrue(AppriseMedium.send(self.event, [destination]))

        self.assertEqual(len(webhook.payloads), 1)
        payload = webhook.payloads[0]
        self.assertTrue(payload["title"].startswith(settings.NOTIFICATION_SUBJECT_PREFIX))
        self.assertIn(self.incident.description, payload["title"])
        self.assertIn(f"Status: {self.event.type}", payload["message"])  # the template uses the raw code
        self.assertIn(f"Actor: {self.event.actor.username}", payload["message"])
        self.assertIn(self.incident.description, payload["message"])

    def test_given_notify_type_should_post_it_as_the_payload_type(self):
        webhook, destination = self._webhook_destination()

        AppriseMedium.send(self.event, [destination], notify_type="warning")

        self.assertEqual(webhook.payloads[0]["type"], "warning")

    def test_given_multiple_destinations_should_post_to_all_of_them(self):
        webhook1, destination1 = self._webhook_destination()
        webhook2, destination2 = self._webhook_destination()

        self.assertTrue(AppriseMedium.send(self.event, [destination1, destination2]))

        self.assertEqual(len(webhook1.payloads), 1)
        self.assertEqual(len(webhook2.payloads), 1)

    def test_when_the_destination_errors_should_return_false(self):
        webhook, destination = self._webhook_destination(response_status=500)

        self.assertFalse(AppriseMedium.send(self.event, [destination]))

        self.assertEqual(len(webhook.payloads), 1)

    def test_when_only_some_destinations_error_should_return_true(self):
        good, good_destination = self._webhook_destination()
        bad, bad_destination = self._webhook_destination(response_status=500)

        self.assertTrue(AppriseMedium.send(self.event, [good_destination, bad_destination]))

        self.assertEqual(len(good.payloads), 1)
        self.assertEqual(len(bad.payloads), 1)

    def test_given_a_url_apprise_cannot_route_should_return_false(self):
        destination = self._destination_for("https://example.com/hook")

        self.assertFalse(AppriseMedium.send(self.event, [destination]))

    def test_when_the_destination_refuses_the_connection_should_return_false(self):
        webhook, destination = self._webhook_destination()
        webhook.stop()

        self.assertFalse(AppriseMedium.send(self.event, [destination]))
