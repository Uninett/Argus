from unittest.mock import patch

from django.test import TestCase, tag
from django.utils.timezone import now

from argus.versioncheck.models import PyPIVersion
from argus.versioncheck.utils import (
    VersionCheckError,
    fetch_info_from_pypi,
    fetch_latest_version_and_upload_time,
    get_latest_registered_version,
    register_and_return_latest_version,
    _get_latest_version_from_pypi_dump,
    _get_latest_upload_time_for_version_from_pypi_dump,
)


@tag("unittest")
class TestFetchInfoFromPyPI(TestCase):
    @patch("argus.versioncheck.utils.requests.get")
    def test_it_should_return_json_on_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [1, 2, 3]
        dump = fetch_info_from_pypi()
        self.assertEqual(dump, [1, 2, 3])

    @patch("argus.versioncheck.utils.requests.get")
    def test_it_should_raise_VersionCheckError_on_failure(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.side_effect = VersionCheckError
        with self.assertRaises(VersionCheckError):
            fetch_info_from_pypi()


@tag("unittest")
class TestFetchLatestVersionAndUploadTime(TestCase):
    @patch("argus.versioncheck.utils.fetch_info_from_pypi")
    def test_golden_path(self, fetch_info_from_pypi):
        with patch("argus.versioncheck.utils._get_latest_version_from_pypi_dump") as versionparser:
            versionparser.return_value = "foo"
            with patch(
                "argus.versioncheck.utils._get_latest_upload_time_for_version_from_pypi_dump"
            ) as uploadtimeparser:
                uploadtimeparser.return_value = "bar"
                latest_version, upload_time = fetch_latest_version_and_upload_time()
                self.assertEqual(latest_version, "foo")
                self.assertEqual(upload_time, "bar")

    @patch("argus.versioncheck.utils.fetch_info_from_pypi")
    def test_when_malformed_version_raise_VersionCheckError(self, fetch_info_from_pypi):
        with self.assertRaises(VersionCheckError):
            fetch_latest_version_and_upload_time()

    @patch("argus.versioncheck.utils.fetch_info_from_pypi")
    def test_when_malformed_releases_raise_VersionCheckError(self, fetch_info_from_pypi):
        with patch("argus.versioncheck.utils._get_latest_version_from_pypi_dump"):
            with self.assertRaises(VersionCheckError):
                fetch_latest_version_and_upload_time()


@tag("database")
class TestGetLatestRegisteredVersion(TestCase):
    def test_golden_path(self):
        versionobj = PyPIVersion.objects.create(version="1.2.3", upload_time=now())
        result = get_latest_registered_version()
        self.assertEqual(result, versionobj)

    def test_when_not_found_and_not_suppressed_raise_VersionCheckError(self):
        with self.assertRaises(VersionCheckError):
            get_latest_registered_version(suppress_errors=False)

    def test_when_not_found_and_suppressed_return_None(self):
        result = get_latest_registered_version()
        self.assertIsNone(result)


@tag("database")
class TestRegisterAndReturnLatestVersion(TestCase):
    @patch("argus.versioncheck.utils.fetch_latest_version_and_upload_time")
    def test_golden_path(self, fetch):
        timestamp = "2020-11-02T06:54:46.156646Z"
        version = "1.2.3"
        fetch.return_value = (version, timestamp)
        result, created = register_and_return_latest_version()
        self.assertTrue(created)
        self.assertEqual(result.version, version)
        self.assertEqual(result.upload_time, timestamp)

    @patch("argus.versioncheck.utils.fetch_info_from_pypi")
    def test_when_error_and_suppress_error_return_None_None(self, fetch):
        fetch.return_value = {}
        result = register_and_return_latest_version()
        self.assertEqual(result, (None, None))

    @patch("argus.versioncheck.utils.fetch_info_from_pypi")
    def test_when_error_and_not_suppress_error_raise_VersionCheckError(self, fetch):
        fetch.return_value = {}
        with self.assertRaises(VersionCheckError):
            register_and_return_latest_version(suppress_errors=False)


@tag("unittest")
class TestPyPIParserHelpers(TestCase):
    def test_when_dump_ok_then_get_latest_version_from_pypi_dump_returns_version(self):
        timestamp = "2020-11-02T06:54:46.156646Z"
        version = "1.2.3"
        dummy_pypi_response = {
            "info": {
                "version": version,
            },
            "releases": {
                version: [
                    {
                        "upload_time_iso_8601": timestamp,
                    },
                ],
            },
        }
        result = _get_latest_version_from_pypi_dump(dummy_pypi_response)
        self.assertEqual(version, result)

    def test_when_dump_bad_then_get_latest_version_from_pypi_dump_raises_KeyError(self):
        dummy_pypi_response = {}
        with self.assertRaises(KeyError):
            _get_latest_version_from_pypi_dump(dummy_pypi_response)

    def test_when_dump_ok_then_get_latest_upload_time_for_version_from_pypi_dump_returns_upload_time(self):
        timestamp = "2020-11-02T06:54:46.156646Z"
        version = "1.2.3"
        dummy_pypi_response = {
            "info": {
                "version": version,
            },
            "releases": {
                version: [
                    {
                        "upload_time_iso_8601": timestamp,
                    },
                ],
            },
        }
        result = _get_latest_upload_time_for_version_from_pypi_dump(dummy_pypi_response, version)
        self.assertEqual(timestamp, result)

    def test_when_dump_bad_then_get_latest_upload_time_for_version_from_pypi_dump_raises_KeyError(self):
        dummy_pypi_response = {}
        with self.assertRaises(KeyError):
            _get_latest_upload_time_for_version_from_pypi_dump(dummy_pypi_response, "blbl")
