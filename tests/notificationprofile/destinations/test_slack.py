from django.test import TestCase, tag
from rest_framework.test import APIRequestFactory

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import DestinationConfigFactory
from argus.notificationprofile.models import Media
from argus.notificationprofile.v2.serializers import RequestDestinationConfigSerializer


@tag("integration")
class SlackNotificationBasicBehaviorTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.request_factory = APIRequestFactory()

    def test_given_valid_request_should_create_slack_destination(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "slack",
            "settings": {
                "destination_url": "https://hooks.slack.com/services/AAA/BBB/CCC",
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
                "destination_url": "https://hooks.slack.com/services/AAA/BBB/CCC",
            },
        )

    def test_given_valid_request_should_update_slack_destination(self):
        destination = DestinationConfigFactory(
            user=self.user,
            media=Media.objects.get(slug="slack"),
            settings={"destination_url": "https://hooks.slack.com/services/AAA/BBB/CCC"},
        )
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "slack",
            "settings": {
                "destination_url": "https://hooks.slack.com/services/CCC/BBB/AAA",
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.update(destination, validated_data)
        self.assertEqual(obj.settings["destination_url"], "https://hooks.slack.com/services/CCC/BBB/AAA")

    def test_given_invalid_medium_slack_destination_serializer_should_not_be_valid(self):
        request = self.request_factory.post("/")
        request.user = self.user

        serializer = RequestDestinationConfigSerializer(
            data={
                "media": "slack",
                "settings": {
                    "destination_url": "https://hooks.slack.com/services/AAA/BBB/CCC",
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
