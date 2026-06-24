from unittest.mock import patch

from django.test import TestCase, tag

from argus.versioncheck.models import LastSeenVersion
from django.core.management import call_command
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
        call_command("check_version", "--save")
        assert LastSeenVersion.objects.filter(version="1.2.3").exists()

    @patch("argus.versioncheck.tasks.get_latest_version")
    def test_when_new_version_is_already_registered_then_do_not_register_it_again(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        LastSeenVersion.objects.create(version="1.2.3")
        assert LastSeenVersion.objects.filter(version="1.2.3").count() == 1
        call_command("check_version", "--save")
        # Still only one instance of this version in the database
        assert LastSeenVersion.objects.filter(version="1.2.3").count() == 1

    @patch("argus.versioncheck.tasks.get_latest_version")
    def test_when_save_flag_is_not_set_then_do_not_register_new_version(self, get_latest_version):
        get_latest_version.return_value = "1.2.3"
        assert not LastSeenVersion.objects.filter(version="1.2.3").exists()
        call_command("check_version")
        assert not LastSeenVersion.objects.filter(version="1.2.3").exists()
