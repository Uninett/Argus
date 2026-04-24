from unittest.mock import patch

from django.test import TestCase, tag
from requests import RequestException

from argus.versioncheck.models import LastSeenVersion
from argus.versioncheck.tasks import task_register_latest_version, get_latest_version
from argus.util.testing import connect_signals, disconnect_signals


@tag("database")
class TestTaskRegisterLatestVersion(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    @patch("argus.versioncheck.tasks.get_latest_version")
    def test_when_new_version_is_not_already_registered_then_register_new_version(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        assert not LastSeenVersion.objects.filter(version="1.2.3").exists()
        task_register_latest_version.func()
        assert LastSeenVersion.objects.filter(version="1.2.3").exists()

    @patch("argus.versioncheck.tasks.get_latest_version")
    def test_when_new_version_is_already_registered_then_do_not_register_it_again(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        LastSeenVersion.objects.create(version="1.2.3")
        assert LastSeenVersion.objects.filter(version="1.2.3").count() == 1
        task_register_latest_version.func()
        # Still only one instance of this version in the database
        assert LastSeenVersion.objects.filter(version="1.2.3").count() == 1

    @patch("argus.versioncheck.tasks.get_latest_version")
    def test_when_a_request_exception_occurs_then_do_not_raise_exception(self, get_latest_version):
        get_latest_version.side_effect = RequestException
        try:
            task_register_latest_version.func()
        except RequestException:
            self.fail("task_register_latest_version raised RequestException unexpectedly!")


@tag("unittest")
class TestGetLatestVersion(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    @patch("argus.versioncheck.tasks.requests.get")
    def test_it_should_return_correct_version(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"info": {"version": "1.2.3"}}
        version = get_latest_version()
        self.assertEqual(version, "1.2.3")
