from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, tag
from django.utils.timezone import now
from requests import RequestException

from argus.versioncheck.models import LastSeenVersion
from argus.versioncheck.utils import get_latest_version, register_latest_version, update_latest_version_on_access
from argus.util.testing import connect_signals, disconnect_signals


@tag("database")
class TestRegisterLatestVersion(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    @patch("argus.versioncheck.utils.get_latest_version")
    def test_when_new_version_is_not_already_registered_then_register_new_version(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        assert not LastSeenVersion.objects.filter(version="1.2.3").exists()
        register_latest_version()
        assert LastSeenVersion.objects.filter(version="1.2.3").exists()

    @patch("argus.versioncheck.utils.get_latest_version")
    def test_when_new_version_is_already_registered_then_do_not_register_it_again(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        LastSeenVersion.objects.create(version="1.2.3")
        assert LastSeenVersion.objects.filter(version="1.2.3").count() == 1
        register_latest_version()
        # Still only one instance of this version in the database
        assert LastSeenVersion.objects.filter(version="1.2.3").count() == 1

    @patch("argus.versioncheck.utils.get_latest_version")
    def test_when_a_request_exception_occurs_then_do_not_raise_exception(self, get_latest_version):
        get_latest_version.side_effect = RequestException
        try:
            register_latest_version()
        except RequestException:
            self.fail("register_latest_version raised RequestException unexpectedly!")


@tag("unittest")
class TestGetLatestVersion(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    @patch("argus.versioncheck.utils.requests.get")
    def test_it_should_return_correct_version(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"info": {"version": "1.2.3"}}
        version = get_latest_version()
        self.assertEqual(version, "1.2.3")


@tag("unittest")
class TestUpdateLatestVersionOnAccess(TestCase):
    @patch("argus.versioncheck.utils.get_latest_version")
    def test_when_no_version_stored_then_get_latest_version(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        version = update_latest_version_on_access()
        self.assertEqual(version, "1.2.3")
        self.assertTrue(LastSeenVersion.objects.exists())

    @patch("argus.versioncheck.utils.get_latest_version")
    def test_when_version_stored_recently_then_do_not_get_latest_version(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        LastSeenVersion.objects.create(timestamp=now, version="1.2.0")
        with patch("argus.versioncheck.utils.now") as tznow:
            tznow.return_value = now() - timedelta(minutes=5)
            version = update_latest_version_on_access()
        self.assertEqual(version, "1.2.0")

    @patch("argus.versioncheck.utils.get_latest_version")
    def test_when_version_stored_long_ago_then_get_latest_version(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        timestamp = now() - timedelta(days=10)
        LastSeenVersion.objects.create(timestamp=timestamp, version="1.2.0")
        version = update_latest_version_on_access()
        self.assertEqual(version, "1.2.3")
