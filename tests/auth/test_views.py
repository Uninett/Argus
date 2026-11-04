from django.test import tag

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import AdminUserFactory, BaseUserFactory


def setup(obj):
    obj.user1 = AdminUserFactory(username="user1")
    obj.user2 = BaseUserFactory(username="user2")

    obj.user1_rest_client = APIClient()
    obj.user1_rest_client.force_authenticate(user=obj.user1)
    obj.user2_rest_client = APIClient()
    obj.user2_rest_client.force_authenticate(user=obj.user2)


@tag("API", "integration")
class CurrentUserViewTests(APITestCase):
    def setUp(self):
        setup(self)

    def test_can_get_admin_url_if_user_is_staff(self):
        response = self.user1_rest_client.get(path="/api/v2/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("admin", response.data["admin_url"])

    def test_cannot_get_admin_url_if_user_is_not_staff(self):
        response = self.user2_rest_client.get(path="/api/v2/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["admin_url"])

    def test_can_get_current_user(self):
        response = self.user1_rest_client.get(path="/api/v2/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user1.username)


@tag("API", "integration")
class UserViewTests(APITestCase):
    def setUp(self):
        setup(self)

    def test_admin_can_get_specific_user(self):
        response = self.user1_rest_client.get(path=f"/api/v2/auth/users/{self.user2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "user2")

    def test_non_admin_cannot_get_specific_user(self):
        response = self.user2_rest_client.get(path=f"/api/v2/auth/users/{self.user2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
