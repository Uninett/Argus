from unittest.mock import patch

from django.test import RequestFactory, TestCase, tag

from argus.auth.factories import AdminUserFactory, PersonUserFactory
from argus.util.testing import connect_signals, disconnect_signals
from argus.versioncheck.context_processors import update_available
from argus.versioncheck.models import LastSeenVersion


@tag("database")
class TestUpdateAvailableContextProcessor(TestCase):
    def setUp(self):
        disconnect_signals()
        self.factory = RequestFactory()

    def tearDown(self):
        connect_signals()

    def _request_for(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_given_non_staff_user_when_newer_version_exists_then_update_available_is_false(self):
        LastSeenVersion.objects.create(version="999.0.0")
        request = self._request_for(PersonUserFactory())
        context = update_available(request)
        assert context == {"update_available": False, "latest_seen_version": None}

    def test_staff_user_sees_no_update_when_table_is_empty(self):
        request = self._request_for(AdminUserFactory())
        context = update_available(request)
        assert not context["update_available"]
        assert context["latest_seen_version"] is None

    @patch("argus.versioncheck.context_processors.get_version")
    def test_staff_user_sees_update_when_newer_version_is_seen(self, get_version):
        get_version.return_value = "1.0.0"
        LastSeenVersion.objects.create(version="1.1.0")
        request = self._request_for(AdminUserFactory())
        context = update_available(request)
        assert context["update_available"]
        assert context["latest_seen_version"] == "1.1.0"

    @patch("argus.versioncheck.context_processors.get_version")
    def test_staff_user_sees_no_update_when_current_version_is_latest(self, get_version):
        get_version.return_value = "1.1.0"
        LastSeenVersion.objects.create(version="1.1.0")
        request = self._request_for(AdminUserFactory())
        context = update_available(request)
        assert not context["update_available"]

    @patch("argus.versioncheck.context_processors.get_version")
    def test_given_dev_build_of_latest_release_when_checking_then_update_available_is_false(self, get_version):
        # Regression test: a setuptools-scm dev version of an already-released
        # version must not be flagged as outdated relative to itself.
        get_version.return_value = "2.8.0.post44+g58afd3be.d20260424"
        LastSeenVersion.objects.create(version="2.8.0")
        request = self._request_for(AdminUserFactory())
        context = update_available(request)
        assert not context["update_available"]

    @patch("argus.versioncheck.context_processors.get_version")
    def test_given_out_of_order_insertion_when_checking_then_takes_max_seen_version(self, get_version):
        get_version.return_value = "1.0.0"
        LastSeenVersion.objects.create(version="1.5.0")
        LastSeenVersion.objects.create(version="1.2.0")
        request = self._request_for(AdminUserFactory())
        context = update_available(request)
        assert context["latest_seen_version"] == "1.5.0"

    def test_given_unparseable_version_row_when_checking_then_it_is_ignored(self):
        LastSeenVersion.objects.create(version="not-a-version")
        request = self._request_for(AdminUserFactory())
        context = update_available(request)
        assert not context["update_available"]
        assert context["latest_seen_version"] is None
