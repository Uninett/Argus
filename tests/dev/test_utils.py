from django.test import TestCase

from argus.dev.utils import StressTester, DatabaseMismatchError

from argus.util.testing import connect_signals, disconnect_signals


class StressTesterTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.stresstester = StressTester("http://localhost.com", "token", 10, 1)

    def tearDown(self):
        connect_signals()

    def test_verify_tags_raise_error_for_incorrect_tags(self):
        expected_data = {
            "tags": [{"tag": "tag1=value1"}, {"tag": "tag2=value2"}],
        }
        actual_data = {
            "tags": [{"tag": "tag1=value2"}, {"tag": "tag2=value1"}],
        }
        with self.assertRaises(DatabaseMismatchError):
            self.stresstester._verify_tags(actual_data, expected_data)

    def test_verify_tags_does_not_raise_exception_for_correct_tags(self):
        expected_data = {
            "tags": [{"tag": "tag1=value1"}, {"tag": "tag2=value2"}],
        }
        actual_data = {
            "tags": [{"tag": "tag1=value1"}, {"tag": "tag2=value2"}],
        }
        self.stresstester._verify_tags(actual_data, expected_data)

    def test_verify_description_raise_error_for_incorrect_description(self):
        expected_data = {
            "description": "correct description",
        }
        actual_data = {
            "description": "incorrect description",
        }
        with self.assertRaises(DatabaseMismatchError):
            self.stresstester._verify_description(actual_data, expected_data)

    def test_verify_description_does_not_raise_exception_for_correct_description(self):
        expected_data = {
            "description": "correct description",
        }
        actual_data = {
            "description": "correct description",
        }
        self.stresstester._verify_description(actual_data, expected_data)

    def test_get_auth_header_returns_correct_header_values(self):
        self.assertEqual(self.stresstester._get_auth_header(), {"Authorization": f"Token token"})

    def test_get_incidents_v1_url_returns_correct_url(self):
        self.assertEqual(self.stresstester._get_incidents_v1_url(), "http://localhost.com/api/v1/incidents/")

    def test_get_incidents_v2_url_returns_correct_url(self):
        self.assertEqual(self.stresstester._get_incidents_v2_url(), "http://localhost.com/api/v2/incidents/")
