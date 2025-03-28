from unittest.mock import Mock

from django import test
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse, HttpResponseRedirect
from django.test.client import RequestFactory
from django_htmx.http import (
    HttpResponseClientRedirect,
    HttpResponseClientRefresh,
    HttpResponseLocation,
)

from argus.htmx.middleware import HtmxMessageMiddleware, LoginRequiredMiddleware


class TestLoginRequiredMiddleware(test.TestCase):
    def setUp(self):
        request = RequestFactory().get("/foo")
        request.login_url = "/login"
        request.user = Mock()
        request.get_full_path = Mock(return_value="/bar")
        self.request = request

    def test_process_view_login_required_false(self):
        def view_func():
            return None

        view_func.login_required = False
        result = LoginRequiredMiddleware(lambda x: x).process_view(self.request, view_func, None, {})
        self.assertIsNone(result)

    @test.override_settings(PUBLIC_URLS=("/foo",))
    def test_process_view_public_urls(self):
        def view_func():
            return None

        result = LoginRequiredMiddleware(lambda x: x).process_view(self.request, view_func, None, {})
        self.assertIsNone(result)

    def test_process_view_authenticated(self):
        def view_func():
            return None

        self.request.user.is_authenticated = True
        result = LoginRequiredMiddleware(lambda x: x).process_view(self.request, view_func, None, {})
        self.assertIsNone(result)
        delattr(self.request.user, "is_authenticated")

    def test_process_view_redirect(self):
        def view_func():
            return None

        self.request.user.is_authenticated = False
        result = LoginRequiredMiddleware(lambda x: x).process_view(self.request, view_func, None, {})
        self.assertIsNotNone(result)
        self.assertIsInstance(result, HttpResponseRedirect)


class TestHtmxMessageMiddleware(test.TestCase):
    def setUp(self):
        request = RequestFactory().get("/foo")
        request.htmx = True
        request.user = Mock()
        self.request = request

        SessionMiddleware(lambda x: x).process_request(self.request)
        MessageMiddleware(lambda x: x).process_request(self.request)
        messages.info(self.request, "a message")

        self.middleware = HtmxMessageMiddleware(lambda x: x)

    def process_response(self, response: HttpResponse):
        return self.middleware.process_response(self.request, response).content.decode()

    def tearDown(self):
        # expire current messages
        messages.get_messages(self.request)

    def test_adds_message_to_response(self):
        self.assertIn("a message", self.process_response(HttpResponse()))

    def test_doesnt_add_message_to_response_if_not_htmx(self):
        self.request.htmx = False
        self.assertNotIn("a message", self.process_response(HttpResponse()))

    def test_doesnt_add_message_on_redirect_response(self):
        responses = [
            ("redirect", HttpResponseRedirect("/")),
            ("hx-redirect", HttpResponseClientRedirect("/")),
            ("hx-location", HttpResponseLocation("/")),
            ("hx-refresh", HttpResponseClientRefresh()),
        ]
        for name, response in responses:
            with self.subTest(name):
                self.assertNotIn("a message", self.process_response(response))
