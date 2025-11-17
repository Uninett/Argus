from django.http import Http404
from django.test import TestCase, RequestFactory
from django.urls import reverse
from argus.auth.factories import PersonUserFactory

from rest_framework import status

from argus.site.views import error


class TestAPIV1GoneView(TestCase):
    def test_api_v1_root_returns_410_on_access(self):
        for path in ("/api/v1/", "/api/v1/gurglefoomimi"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_410_GONE)


class TestErrorView(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.factory = RequestFactory()

    def test_error_view_bad_requests(self):
        # No status code provided
        request = self.factory.get(reverse("error"))
        request.user = self.user
        response = error(request)
        self.assertEqual(response.status_code, 400)

        # Status code is not a valid int
        request = self.factory.get(reverse("error"), {"status-code": "not-a-number"})
        request.user = self.user
        response = error(request)
        self.assertEqual(response.status_code, 400)

        # Status code not supported
        request = self.factory.get(reverse("error"), {"status-code": "666"})
        request.user = self.user
        response = error(request)
        self.assertEqual(response.status_code, 400)

    def test_error_view_valid_status_codes(self):
        status_codes = [400, 403, 410]

        for status_code in status_codes:
            with self.subTest(status_code=status_code):
                request = self.factory.get(reverse("error"), {"status-code": str(status_code)})
                request.user = self.user
                response = error(request)
                self.assertEqual(response.status_code, status_code)
                self.assertIn(str(status_code), response.content.decode())

    def test_error_view_404(self):
        request = self.factory.get(reverse("error"), {"status-code": "404"})
        request.user = self.user
        with self.assertRaises(Http404):
            response = error(request)
            self.assertEqual(response.status_code, 404)
            self.assertIn(str(404), response.content.decode())

    def test_error_view_500(self):
        request = self.factory.get(reverse("error"), {"status-code": "500"})
        request.user = self.user
        with self.assertRaises(Exception):
            response = error(request)
            self.assertEqual(response.status_code, 500)
            self.assertIn(str(500), response.content.decode())
