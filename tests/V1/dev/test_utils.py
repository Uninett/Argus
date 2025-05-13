from django.test import TestCase

from argus.dev.utils import StressTester

from argus.util.testing import disconnect_signals


class StressTesterTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.stresstester = StressTester("http://localhost.com", "token", 10, 1)

    def test_get_incidents_v1_url_returns_correct_url(self):
        self.assertEqual(self.stresstester._get_incidents_v1_url(), "http://localhost.com/api/v1/incidents/")
