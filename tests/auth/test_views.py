from django.test import override_settings, tag

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import AdminUserFactory, BaseUserFactory
from argus.util.testing import disconnect_signals, connect_signals


@tag("API", "integration")
class ViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        self.user1 = AdminUserFactory(username="user1")
        self.user2 = BaseUserFactory(username="user2")

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)
        self.user2_rest_client = APIClient()
        self.user2_rest_client.force_authenticate(user=self.user2)

    def teardown(self):
        connect_signals()

    def test_can_get_specific_user(self):
        response = self.user1_rest_client.get(path=f"/api/v2/auth/users/{self.user2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "user2")

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

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "argus.dataporten.social.DataportenFeideOAuth2",
            "django.contrib.auth.backends.RemoteUserBackend",
            "django.contrib.auth.backends.ModelBackend",
        ]
    )
    def test_can_get_login_methods(self):
        response = self.user1_rest_client.get(path="/login-methods/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            [
                {"type": "username_password", "url": "http://testserver/api/v1/token-auth/", "name": "user_pw"},
                {"type": "OAuth2", "url": "http://testserver/oidc/login/dataporten_feide/", "name": "dataporten_feide"},
            ],
        )
