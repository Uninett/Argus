from unittest.mock import Mock, patch

from django import test
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect
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

    @patch("argus.htmx.middleware.LOG")
    def test_process_exception_logs_traceback_and_adds_error_message(self, mock_log):
        exception = ValueError("Something went wrong")
        result = self.middleware.process_exception(self.request, exception)

        self.assertIsNone(result)
        mock_log.exception.assert_called_once_with("HTMX request failed: %s", "ValueError: Something went wrong")

        # Check that the error message was added to messages
        storage = messages.get_messages(self.request)
        message_list = list(storage)
        self.assertEqual(len(message_list), 2)
        self.assertIn("ValueError: Something went wrong", [m.message for m in message_list])

    @patch("argus.htmx.middleware.LOG")
    def test_process_exception_handles_exception_without_message(self, mock_log):
        exception = ValueError()
        self.middleware.process_exception(self.request, exception)

        mock_log.exception.assert_called_once_with("HTMX request failed: %s", "ValueError")

        storage = messages.get_messages(self.request)
        message_list = list(storage)
        self.assertIn("ValueError", [m.message for m in message_list])

    @patch("argus.htmx.middleware.LOG")
    def test_process_response_error_without_message_adds_status_code(self, mock_log):
        # Clear existing messages
        list(messages.get_messages(self.request))

        response = self.middleware.process_response(self.request, HttpResponseNotFound())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Retarget"), "#notification-messages .toast")
        mock_log.error.assert_called_once_with("HTMX request returned %s for %s %s", "404: Not Found", "GET", "/foo")

    @patch("argus.htmx.middleware.LOG")
    def test_process_response_error_with_existing_message_doesnt_add_generic(self, mock_log):
        # Clear existing messages and add an error message
        list(messages.get_messages(self.request))
        messages.error(self.request, "Custom error message")

        response = self.middleware.process_response(self.request, HttpResponseBadRequest())

        self.assertEqual(response.status_code, 200)
        mock_log.error.assert_not_called()

        # Verify the custom message is preserved
        self.assertIn("Custom error message", response.content.decode())

    @patch("argus.htmx.middleware.LOG")
    def test_process_response_error_returns_200_with_htmx_headers(self, mock_log):
        list(messages.get_messages(self.request))

        response = self.middleware.process_response(self.request, HttpResponseNotFound())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Retarget"), "#notification-messages .toast")
        self.assertEqual(response.headers.get("HX-Reswap"), "beforeend")
