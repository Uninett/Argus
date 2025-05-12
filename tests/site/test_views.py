from django.test import TestCase

from rest_framework import status


class TestAPIV1GoneView(TestCase):
    def test_api_v1_root_returns_410_on_access(self):
        for path in ("/api/v1/", "/api/v1/gurglefoomimi"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_410_GONE)
