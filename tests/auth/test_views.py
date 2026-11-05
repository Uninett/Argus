from django.test import tag

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import AdminUserFactory, BaseUserFactory


def setup(obj):
    obj.adminuser = AdminUserFactory(username="adminuser")
    obj.normaluser = BaseUserFactory(username="normaluser")

    obj.adminuser_rest_client = APIClient()
    obj.adminuser_rest_client.force_authenticate(user=obj.adminuser)
    obj.normaluser_rest_client = APIClient()
    obj.normaluser_rest_client.force_authenticate(user=obj.normaluser)


@tag("API", "integration")
class CurrentUserViewTests(APITestCase):
    def setUp(self):
        setup(self)

    def test_can_get_admin_url_if_user_is_staff(self):
        response = self.adminuser_rest_client.get(path="/api/v2/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("admin", response.data["admin_url"])

    def test_cannot_get_admin_url_if_user_is_not_staff(self):
        response = self.normaluser_rest_client.get(path="/api/v2/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["admin_url"])

    def test_can_get_current_user(self):
        response = self.adminuser_rest_client.get(path="/api/v2/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.adminuser.username)


@tag("API", "integration")
class UserViewTests(APITestCase):
    def setUp(self):
        setup(self)

    def test_given_admin_requestor_then_successfully_get_any_specific_user(self):
        response = self.adminuser_rest_client.get(path=f"/api/v2/auth/users/{self.adminuser.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "adminuser")

        response = self.adminuser_rest_client.get(path=f"/api/v2/auth/users/{self.normaluser.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "normaluser")

    def test_given_non_admin_requestor_then_fail_to_get_any_specific_user(self):
        response = self.normaluser_rest_client.get(path=f"/api/v2/auth/users/{self.normaluser.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.normaluser_rest_client.get(path=f"/api/v2/auth/users/{self.adminuser.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
