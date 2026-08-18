from django import test
from django.test.client import RequestFactory

from argus.auth.factories import PersonUserFactory
from argus.htmx.incident.constants import PAGE_SIZE_DEFAULT
from argus.htmx.incident.views import incident_list
from argus.htmx.user.factories import ArgusHtmxPreferencesFactory
from argus.incident.constants import Level
from argus.incident.factories import IncidentFactory
from argus.util.testing import connect_signals, disconnect_signals


class TestSortingPreservation(test.TestCase):
    def setUp(self):
        disconnect_signals()
        self.addCleanup(connect_signals)

        IncidentFactory.create_batch(PAGE_SIZE_DEFAULT + 1)
        request = RequestFactory().get(
            "/incidents",
            {"sort": "level", "sort_order": "asc", "maxlevel": max(Level).value},
        )
        request.session = {}
        request.user = PersonUserFactory()
        request.htmx = False
        preferences = ArgusHtmxPreferencesFactory(user=request.user)
        preferences.preferences["incidents_table_column_name"] = "default"
        preferences.save()
        self.response = incident_list(request)

    def test_given_non_default_sort_then_autorefresh_hx_vals_should_include_current_sort(self):
        self.assertContains(self.response, '"page": "1", "sort": "level", "sort_order": "asc"')

    def test_given_non_default_sort_and_multiple_pages_then_pagination_link_hx_vals_should_include_current_sort(self):
        self.assertContains(self.response, '"page": "2", "sort": "level", "sort_order": "asc"')
