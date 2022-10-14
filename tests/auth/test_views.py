from django.test import tag

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import AdminUserFactory, BaseUserFactory
from argus.util.testing import disconnect_signals, connect_signals


@tag("API", "integration")
class ViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        self.user1 = AdminUserFactory(username="user1")

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

    def teardown(self):
        connect_signals()

    def test_can_get_specific_user(self):
        user2_pk = BaseUserFactory(username="user2").pk
        response = self.user1_rest_client.get(path=f"/api/v2/auth/users/{user2_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "user2")

    def test_can_get_current_user(self):
        response = self.user1_rest_client.get(path="/api/v2/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user1.username)
