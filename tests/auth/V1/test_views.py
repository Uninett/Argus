from django.test import tag

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import AdminUserFactory, BaseUserFactory
from argus.notificationprofile.factories import DestinationConfigFactory
from argus.notificationprofile.models import DestinationConfig, Media
from argus.util.testing import disconnect_signals, connect_signals


@tag("API", "integration")
class ViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        self.user1 = AdminUserFactory(username="user1")

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        self.sms_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474700"},
        )

    def teardown(self):
        connect_signals()

    def test_can_get_specific_phone_number(self):
        phone_number_pk = self.sms_destination.pk
        response = self.user1_rest_client.get(path=f"/api/v1/auth/phone-number/{phone_number_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], phone_number_pk)

    def test_can_get_all_phone_numbers(self):
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474701"},
        )
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474702"},
        )
        response = self.user1_rest_client.get(path="/api/v1/auth/phone-number/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        phone_numbers = self.user1.destinations.filter(media_id="sms")
        self.assertEqual(len(response.data), len(phone_numbers))
        phone_number_pks = set([phone_number.pk for phone_number in phone_numbers])
        response_pks = set([phone_number["pk"] for phone_number in response.data])
        self.assertEqual(response_pks, phone_number_pks)

    def test_can_create_phone_number_with_valid_values(self):
        response = self.user1_rest_client.post(
            path="/api/v1/auth/phone-number/",
            data={"phone_number": "+4747474747"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DestinationConfig.objects.filter(pk=response.data["pk"]).exists())

    def test_cannot_create_phone_number_with_invalid_phone_number(self):
        settings = {"phone_number": "+470"}
        response = self.user1_rest_client.post(
            path="/api/v1/auth/phone-number/",
            data=settings,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(DestinationConfig.objects.filter(media_id="sms", settings=settings).exists())

    def test_cannot_create_duplicate_phone_number(self):
        settings = {"phone_number": "+4747474701"}
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings=settings,
        )
        response = self.user1_rest_client.post(
            path="/api/v1/auth/phone-number/",
            data=settings,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DestinationConfig.objects.filter(media_id="sms", settings=settings).count(), 1)

    def test_can_update_phone_number_with_valid_values(self):
        new_settings = {"phone_number": "+4747474702"}
        destination_pk = DestinationConfigFactory(
            user=self.user1, media=Media.objects.get(slug="sms"), settings={"phone_number": "+4747474701"}
        ).pk
        response = self.user1_rest_client.patch(
            path=f"/api/v1/auth/phone-number/{destination_pk}/",
            data=new_settings,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DestinationConfig.objects.get(pk=destination_pk).settings, new_settings)

    def test_cannot_update_phone_number_with_duplicate_phone_number(self):
        settings1 = {"phone_number": "+4747474701"}
        settings2 = {"phone_number": "+4747474702"}
        DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings=settings1,
        )
        destination_pk = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings=settings2,
        ).pk
        response = self.user1_rest_client.patch(
            path=f"/api/v1/auth/phone-number/{destination_pk}/",
            data=settings1,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DestinationConfig.objects.get(pk=destination_pk).settings, settings2)

    def test_can_delete_phone_number(self):
        phone_number_pk = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474701"},
        ).pk
        response = self.user1_rest_client.delete(f"/api/v1/auth/phone-number/{phone_number_pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DestinationConfig.objects.filter(pk=phone_number_pk).exists())

    def test_can_get_specific_user(self):
        user2_pk = BaseUserFactory(username="user2").pk
        response = self.user1_rest_client.get(path=f"/api/v1/auth/users/{user2_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "user2")

    def test_can_get_current_user(self):
        response = self.user1_rest_client.get(path="/api/v1/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user1.username)
