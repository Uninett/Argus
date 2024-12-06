from django.test import tag

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed

from argus.auth.factories import BaseUserFactory
from argus.util.testing import disconnect_signals, connect_signals
from argus.auth.knox.views import JsonAuthentication


@tag("unit", "knox")
class JsonAuthenticationTests(APITestCase):
    def setUp(self):
        disconnect_signals()

    def teardown(self):
        connect_signals()

    def test_authenticate_golden_path(self):
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

    def test_authenticate_with_no_request_body_returns_None(self):
        factory = APIRequestFactory()
        request = factory.post("", None, format="json")
        jsonauth = JsonAuthentication()
        result = jsonauth.authenticate(request)
        self.assertIsNone(result)  # allows fall back to next method

    def test_authenticate_croaks_on_invalid_json(self):
        factory = APIRequestFactory()
        request = factory.post("", {}, format="json")
        request._body = b"{"
        jsonauth = JsonAuthentication()
        with self.assertRaises(AuthenticationFailed):
            jsonauth.authenticate(request)

    def test_authenticate_croaks_on_nonexistent_user(self):
        jsonblob = {
            "username": "bvgfyhjuknbnvfgyhjknuhbvfbgyhjtuk",
            "password": "cdfvgbhjjhnuikopl",
        }
        factory = APIRequestFactory()
        request = factory.post("", jsonblob, format="json")
        jsonauth = JsonAuthentication()
        with self.assertRaises(AuthenticationFailed):
            jsonauth.authenticate(request)

    def test_authenticate_croaks_on_inactive_user(self):
        password = "cvbfghcfgvdhyu"
        user = BaseUserFactory(username="user", password=password, is_active=False)
        jsonblob = {
            "username": user.username,
            "password": password,
        }
        factory = APIRequestFactory()
        request = factory.post("", jsonblob, format="json")
        jsonauth = JsonAuthentication()
        with self.assertRaises(AuthenticationFailed):
            jsonauth.authenticate(request)
