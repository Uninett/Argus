from unittest.mock import Mock

from django import test
from django.http import HttpResponseRedirect
from django.test.client import RequestFactory

from argus_htmx.middleware import LoginRequiredMiddleware


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
