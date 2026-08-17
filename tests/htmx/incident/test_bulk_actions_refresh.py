from django import test
from django.test.client import RequestFactory

from argus.auth.factories import PersonUserFactory
from argus.htmx.incident.views import incident_list
from argus.htmx.user.factories import ArgusHtmxPreferencesFactory


class TestBulkActionsHiddenOnIncidentTableRefresh(test.TestCase):
    def setUp(self):
        request = RequestFactory().get("/incidents")
        request.session = {}
        request.user = PersonUserFactory()
        request.htmx = False
        preferences = ArgusHtmxPreferencesFactory(user=request.user)
        preferences.preferences["incidents_table_column_name"] = "default"
        preferences.save()
        self.response = incident_list(request)

    def test_it_should_close_open_dialogs_before_hiding_bulk_actions_when_incident_table_is_refreshed(self):
        self.assertContains(
            self.response,
            "bulkActions?.querySelectorAll('dialog[open]').forEach(dialog => dialog.close());\n"
            "        bulkActions?.classList.add('hidden');",
        )
