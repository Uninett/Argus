from django.test import tag

from rest_framework.test import APITestCase, APIRequestFactory

from argus.auth.factories import BaseUserFactory
from argus.util.testing import disconnect_signals, connect_signals
from argus.auth.knox.views import JsonAuthentication


@tag("unit", "knox")
class JsonAuthenticationTests(APITestCase):
    def setUp(self):
        disconnect_signals()

    def teardown(self):
        connect_signals()

    def test_authenticate_header_returns_None(self):
        jsonauth = JsonAuthentication()
        self.assertIsNone(jsonauth.authenticate_header(None))

    def test_authenticate(self):
        password = "cvbfghcfgvdhyu"
        user = BaseUserFactory(username="user", password=password)
        jsonblob = {
            "username": user.username,
            "password": password,
        }
        factory = APIRequestFactory()
        request = factory.post("", jsonblob, format="json")
        jsonauth = JsonAuthentication()
        result_user, _ = jsonauth.authenticate(request)
        self.assertEqual(result_user, user)
