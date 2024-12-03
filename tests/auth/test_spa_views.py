from django.test import override_settings, tag

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import BaseUserFactory
from argus.util.testing import disconnect_signals, connect_signals


@tag("API", "integration", "spa")
@override_settings(
    ROOT_URLCONF="argus.spa.root_urls",
)
class SpaViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        self.user = BaseUserFactory(username="user")

        self.rest_client = APIClient()
        self.rest_client.force_authenticate(user=self.user)

    def teardown(self):
        connect_signals()

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "django.contrib.auth.backends.RemoteUserBackend",
            "django.contrib.auth.backends.ModelBackend",
        ],
    )
    def test_can_get_login_methods(self):
        response = self.rest_client.get(path="/login-methods/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            [
                {"type": "username_password", "url": "http://testserver/api/v1/token-auth/", "name": "user_pw"},
            ],
        )
