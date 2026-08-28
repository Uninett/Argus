from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, tag
from django.utils.timezone import now

from argus.versioncheck.models import PyPIVersion
from argus.versioncheck.utils import register_version


@tag("database")
class TestCheckVersion(TestCase):
    @patch("argus.versioncheck.utils.fetch_latest_version_and_upload_time")
    def test_when_new_version_is_not_already_registered_then_register_new_version(
        self, fetch_latest_version_and_upload_time
    ):
        timestamp = now()
        fetch_latest_version_and_upload_time.return_value = ("1.2.3", timestamp)
        self.assertFalse(PyPIVersion.objects.filter(version="1.2.3").exists())
        call_command("check_version", "--save")
        self.assertTrue(PyPIVersion.objects.filter(version="1.2.3").exists())

    @patch("argus.versioncheck.utils.fetch_latest_version_and_upload_time")
    def test_when_new_version_is_already_registered_then_do_not_register_it_again(
        self, fetch_latest_version_and_upload_time
    ):
        timestamp = now()
        fetch_latest_version_and_upload_time.return_value = ("1.2.3", timestamp)
        register_version("1.2.3", timestamp)
        self.assertEqual(PyPIVersion.objects.filter(version="1.2.3").count(), 1)
        call_command("check_version", "--save")
        # Still only one instance of this version in the database
        self.assertEqual(PyPIVersion.objects.filter(version="1.2.3").count(), 1)

    @patch("argus.versioncheck.utils.fetch_latest_version_and_upload_time")
    def test_when_save_flag_is_not_set_then_do_not_register_new_version(self, fetch_latest_version_and_upload_time):
        timestamp = now()
        fetch_latest_version_and_upload_time.return_value = ("1.2.3", timestamp)
        self.assertFalse(PyPIVersion.objects.filter(version="1.2.3").exists())
        call_command("check_version")
        self.assertFalse(PyPIVersion.objects.filter(version="1.2.3").exists())
