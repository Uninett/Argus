from django.test import tag
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import DestinationConfigFactory
from argus.notificationprofile.models import (
    DestinationConfig,
    Media,
)
from argus.util.testing import connect_signals, disconnect_signals


@tag("API", "integration")
class MediumViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=user1)

    def teardown(self):
        connect_signals()

    def test_should_get_all_media(self):
        response = self.user1_rest_client.get(path="/api/v3/notificationprofiles/media/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(set([medium["slug"] for medium in response.data]), set(["sms", "email"]))

    def test_should_get_specific_medium(self):
        response = self.user1_rest_client.get(path="/api/v3/notificationprofiles/media/email/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["slug"], "email")


@tag("API", "integration")
class DestinationViewTests(APITestCase):
    ENDPOINT = "/api/v3/notificationprofiles/destinations/"

    def setUp(self):
        disconnect_signals()
        user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=user1)

        # Default email destination is automatically created with user
        self.synced_email_destination = user1.destinations.get()
        self.non_synced_email_destination = DestinationConfigFactory(
            user=user1,
            media=Media.objects.get(slug="email"),
            settings={"email_address": "test@example.com"},
            managed=False,
        )
        self.sms_destination = DestinationConfigFactory(
            user=user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474747"},
            managed=None,
        )

    def teardown(self):
        connect_signals()

    def test_should_get_list_of_all_destinations(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 3, response.data)
        response_settings = set()
        # the response should have a synced-key in v2 which is not stored in the database
        for destination in response.data:
            settings = destination["settings"]
            settings.pop("synced", None)
            response_settings.add(tuple(settings.items()))
        self.assertTrue(tuple(self.synced_email_destination.settings.items()) in response_settings)
        self.assertTrue(tuple(self.non_synced_email_destination.settings.items()) in response_settings)
        self.assertTrue(tuple(self.sms_destination.settings.items()) in response_settings)

    def test_should_get_specific_destination(self):
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.synced_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # v2 response has "synced", which is not visible in the database
        self.assertEqual(
            response.data["settings"]["email_address"], self.synced_email_destination.settings["email_address"]
        )

    def test_should_indicate_duplicate_destination_when_it_exists(self):
        DestinationConfigFactory(media_id="sms", settings=self.sms_destination.settings)
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.sms_destination.pk}/duplicate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data["is_duplicate"])

    def test_should_not_indicate_duplicate_destination_when_it_doesnt_exist(self):
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.sms_destination.pk}/duplicate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertFalse(response.data["is_duplicate"])

    def test_should_not_break_on_trying_to_delete_nonexisting_destination(self):
        non_existent_pk = DestinationConfig.objects.last().id + 1
        non_existent_destination_path = f"{self.ENDPOINT}{non_existent_pk}/"
        response = self.user1_rest_client.delete(path=non_existent_destination_path)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
