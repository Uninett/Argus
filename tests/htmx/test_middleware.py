from unittest.mock import Mock, patch

from django import test
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect
from django.conf import settings
from django.test.client import RequestFactory
from django_htmx.http import (
    HttpResponseClientRedirect,
    HttpResponseClientRefresh,
    HttpResponseLocation,
)

from argus.htmx import middleware as middleware_module
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

    @test.override_settings(PUBLIC_URLS=["/api/"], SITE_SUBURL="argus/")
    def test_given_a_sub_path_then_public_urls_should_be_prefixed(self):
        middleware = LoginRequiredMiddleware(lambda x: x)
        self.assertEqual(middleware.public_urls, ("/argus/api/",))

    @test.override_settings(PUBLIC_URLS=["htmx:login"], SITE_SUBURL="argus/")
    def test_given_a_public_url_name_then_it_should_be_resolved_and_prefixed(self):
        middleware = LoginRequiredMiddleware(lambda x: x)
        self.assertEqual(middleware.public_urls, ("/argus/accounts/login/",))

    @test.override_settings(PUBLIC_URLS=["/api/"], SITE_SUBURL="")
    def test_given_no_sub_path_then_public_urls_should_be_left_alone(self):
        middleware = LoginRequiredMiddleware(lambda x: x)
        self.assertEqual(middleware.public_urls, ("/api/",))

    def test_given_no_public_urls_setting_then_there_should_be_none(self):
        middleware = LoginRequiredMiddleware(lambda x: x)
        with test.override_settings():
            del settings.PUBLIC_URLS  # override_settings cannot unset, only override
            self.assertEqual(middleware.public_urls, ())

    @test.override_settings(PUBLIC_URLS=["htmx:no-such-view", "/api/"])
    def test_given_an_unresolvable_entry_then_it_should_be_skipped(self):
        # this middleware is installed even where the htmx urls are not, and
        # raising here would take down every url rather than just this one
        self.forget_unresolvable_warnings()
        middleware = LoginRequiredMiddleware(lambda x: x)
        with self.assertLogs("argus.htmx.middleware", level="WARNING"):
            self.assertEqual(middleware.public_urls, ("/api/",))

    @test.override_settings(PUBLIC_URLS=["htmx:no-such-view"])
    def test_given_an_unresolvable_entry_then_it_should_be_complained_about_once(self):
        # the list is rebuilt per request, so warning every time would fill an
        # access log for as long as the misconfiguration lasts
        self.forget_unresolvable_warnings()
        middleware = LoginRequiredMiddleware(lambda x: x)
        with self.assertLogs("argus.htmx.middleware", level="WARNING") as logged:
            middleware.public_urls
            middleware.public_urls
        self.assertEqual(len(logged.records), 1)

    def test_when_settings_change_after_construction_then_public_urls_should_follow(self):
        # the middleware chain is built once, before the first request, so
        # anything resolved and kept at that point is frozen out of reach
        middleware = LoginRequiredMiddleware(lambda x: x)
        with test.override_settings(PUBLIC_URLS=["/api/"], SITE_SUBURL="argus/"):
            self.assertEqual(middleware.public_urls, ("/argus/api/",))

    def test_when_settings_change_after_first_access_then_public_urls_should_follow(self):
        # nothing is cached, so even a value already read keeps up
        middleware = LoginRequiredMiddleware(lambda x: x)
        self.assertNotIn("/argus/api/", middleware.public_urls)
        with test.override_settings(PUBLIC_URLS=["/api/"], SITE_SUBURL="argus/"):
            self.assertEqual(middleware.public_urls, ("/argus/api/",))

    def forget_unresolvable_warnings(self):
        """Reset the warn-once cache, which otherwise outlives a single test"""
        middleware_module._UNRESOLVABLE_PUBLIC_URLS.clear()
        self.addCleanup(middleware_module._UNRESOLVABLE_PUBLIC_URLS.clear)


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
