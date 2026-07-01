from types import SimpleNamespace

from django import forms, test
from django.test.client import RequestFactory
from django.urls import reverse

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.filter.queryset_filters import QuerySetFilter
from argus.htmx.incident.columns import IncidentTableColumn
from argus.htmx.incident.views import (
    filter_form as filter_form_view,
    filter_select,
    get_form,
    get_incident_ids_to_update,
    incident_detail,
    incident_list,
    incident_list_kiosk,
    KIOSK_URL_NAME,
)
from argus.htmx.user.factories import ArgusHtmxPreferencesFactory
from argus.incident.factories import StatelessIncidentFactory


class IncidentRegularFilterForm(forms.Form):
    description = forms.CharField(max_length=255, required=False)


class IncidentColumnFilterForm(forms.Form):
    description = forms.CharField(max_length=255, required=False)
    description.in_header = True


def incident_list_filter_factory(form_cls):
    def incident_list_filter(request, qs):
        form = form_cls(request.GET or None)

        if form.is_valid():
            filterblob = form.to_filterblob()
            qs = QuerySetFilter.filtered_incidents(filterblob, qs)
        return form, qs

    return incident_list_filter


@test.override_settings(
    ARGUS_HTMX_FILTER_FUNCTION=incident_list_filter_factory(IncidentRegularFilterForm),
    INCIDENT_TABLE_COLUMNS=[
        IncidentTableColumn(
            "description",
            label="Description",
            cell_template="htmx/incidents/_incident_description.html",
        ),
    ],
)
class TestRegularColumn(test.TestCase):
    def setUp(self):
        request = RequestFactory().get("/incidents")
        request.session = {}
        request.user = PersonUserFactory()
        request.htmx = False
        preferences = ArgusHtmxPreferencesFactory(user=request.user)
        preferences.preferences["incidents_table_column_name"] = "default"
        preferences.save()
        self.response = incident_list(request)

    def test_doesnt_add_filter_button_to_header(self):
        self.assertNotContains(self.response, "filter-btn")

    def test_add_filter_to_filterbox(self):
        self.assertContains(self.response, '<span class="label-text">Description</span>')


@test.override_settings(
    ARGUS_HTMX_FILTER_FUNCTION=incident_list_filter_factory(IncidentColumnFilterForm),
    INCIDENT_TABLE_COLUMNS=[
        IncidentTableColumn(
            "search_description",
            label="Description",
            cell_template="htmx/incidents/_incident_description.html",
            filter_field="description",
        ),
    ],
)
class TestFilterableColumn(test.TestCase):
    def setUp(self):
        request = RequestFactory().get("/incidents")
        request.session = {}
        request.user = PersonUserFactory()
        request.htmx = False
        preferences = ArgusHtmxPreferencesFactory(user=request.user)
        preferences.preferences["incidents_table_column_name"] = "default"
        preferences.save()
        self.response = incident_list(request)

    def test_adds_filter_button_to_header(self):
        self.assertContains(self.response, "filter-btn")

    def test_doesnt_add_filter_to_filterbox(self):
        self.assertNotContains(self.response, '<span class="label-text">Description</span>')


@test.override_settings(INCIDENT_TABLE_COLUMNS=["row_select", "id"])
class KioskModeTests(test.TestCase):
    def setUp(self):
        request = RequestFactory().get("/incidents/kiosk/")
        request.session = {}
        self.user = PersonUserFactory()
        request.user = self.user
        request.htmx = False
        preferences = ArgusHtmxPreferencesFactory(user=request.user)
        preferences.preferences["incidents_table_column_name"] = "default"
        preferences.save()
        self.kiosk_response = incident_list(request, kiosk_mode=True)
        self.normal_response = incident_list(request)

    def test_given_kiosk_mode_it_should_remove_interactive_controls(self):
        self.assertNotContains(self.kiosk_response, 'id="col-row_select"')
        self.assertNotContains(self.kiosk_response, 'id="bulk-actions"')

    def test_given_kiosk_mode_it_should_move_stats_to_navbar(self):
        self.assertNotContains(self.kiosk_response, 'id="table-refresh-info"')
        self.assertNotContains(self.kiosk_response, 'id="filter-controls-box"')
        self.assertContains(self.kiosk_response, 'id="kiosk-filtered-count"')
        self.assertContains(self.kiosk_response, 'id="kiosk-last-refreshed"')

    def test_given_normal_mode_it_should_show_interactive_controls_and_footer(self):
        self.assertContains(self.normal_response, 'id="bulk-actions"')
        self.assertContains(self.normal_response, 'id="filter-controls-box"')
        self.assertContains(self.normal_response, 'id="table-refresh-info"')
        self.assertNotContains(self.normal_response, 'id="kiosk-filtered-count"')
        self.assertNotContains(self.normal_response, 'id="kiosk-last-refreshed"')

    def test_given_kiosk_mode_it_should_use_kiosk_url(self):
        self.assertContains(self.kiosk_response, f'hx-get="{reverse(KIOSK_URL_NAME)}"')

    def test_given_kiosk_mode_it_should_show_exit_button_in_navbar(self):
        self.assertContains(self.kiosk_response, f'href="{reverse("htmx:incident-list")}"')

    def test_given_normal_mode_it_should_show_kiosk_button_in_filter_bar(self):
        self.assertContains(self.normal_response, f'href="{reverse(KIOSK_URL_NAME)}"')

    def test_given_kiosk_mode_htmx_refresh_it_should_include_oob_swaps(self):
        request = RequestFactory().get("/incidents/kiosk/")
        request.session = {}
        request.user = self.user
        request.htmx = True
        response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, 'hx-swap-oob="innerHTML:#kiosk-filtered-count"')
        self.assertContains(response, 'hx-swap-oob="innerHTML:#kiosk-last-refreshed"')

    def test_given_kiosk_endpoint_it_should_return_kiosk_response(self):
        request = RequestFactory().get("/incidents/kiosk/")
        request.session = {}
        request.user = self.user
        request.htmx = False
        response = incident_list_kiosk(request)
        self.assertContains(response, 'id="kiosk-filtered-count"')
        self.assertContains(response, 'id="kiosk-last-refreshed"')


@test.override_settings(INCIDENT_TABLE_COLUMNS=["id"])
class FilterSelectTests(test.TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        ArgusHtmxPreferencesFactory(user=self.user)

    def _make_request(self, params=None, trigger=None):
        request = RequestFactory().get("/incidents/", params or {})
        request.session = {}
        request.user = self.user
        request.htmx = SimpleNamespace(trigger=trigger)
        return request

    def test_given_no_trigger_filter_select_it_should_retarget(self):
        response = filter_select(self._make_request())
        self.assertEqual(response.status_code, 200)

    def test_given_trigger_filter_select_it_should_render_filterbox(self):
        response = filter_select(self._make_request(trigger="some-element"))
        self.assertContains(response, 'id="incident-filter-box"')

    def test_given_filter_id_filter_select_it_should_select_filter(self):
        filter_obj = FilterFactory(user=self.user)
        request = self._make_request(params={"filter": filter_obj.pk})
        filter_select(request)
        self.assertEqual(request.session.get("selected_filter"), str(filter_obj.pk))


class FilterFormTests(test.TestCase):
    def test_given_get_request_filter_form_it_should_render_filterbox(self):
        request = RequestFactory().get("/incidents/filter-form/")
        request.session = {}
        request.user = PersonUserFactory()
        request.htmx = False
        response = filter_form_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("selected_filter", request.session)
        self.assertIsNone(request.session["selected_filter"])


@test.override_settings(INCIDENT_TABLE_COLUMNS=["id"])
class IncidentListVariantTests(test.TestCase):
    def _make_request(self, params=None):
        request = RequestFactory().get("/incidents/", params or {})
        request.session = {}
        request.user = PersonUserFactory()
        request.htmx = False
        ArgusHtmxPreferencesFactory(user=request.user)
        return request

    def test_given_non_default_sort_field_it_should_apply_secondary_sort(self):
        response = incident_list(self._make_request({"sort": "level"}))
        self.assertEqual(response.status_code, 200)

    def test_given_timeframe_in_session_it_should_include_timeframe_in_query(self):
        request = self._make_request()
        request.session["timeframe"] = 60  # one hour, stored as int by the form
        response = incident_list(request)
        self.assertEqual(response.status_code, 200)


class IncidentDetailTests(test.TestCase):
    def test_given_existing_incident_it_should_render_detail(self):
        incident = StatelessIncidentFactory()
        request = RequestFactory().get(f"/incidents/{incident.pk}/")
        request.user = PersonUserFactory()
        request.htmx = False
        response = incident_detail(request, pk=incident.pk)
        self.assertEqual(response.status_code, 200)


class UtilityFunctionTests(test.TestCase):
    def test_get_incident_ids_to_update_it_should_return_post_ids(self):
        self.assertEqual(get_incident_ids_to_update(RequestFactory().post("/")), [])
        self.assertEqual(
            get_incident_ids_to_update(RequestFactory().post("/", {"incident_ids": ["1", "2"]})),
            ["1", "2"],
        )

    def test_get_form_it_should_return_form_only_when_post_data_present(self):
        self.assertIsNone(get_form(RequestFactory().get("/"), forms.Form))
        self.assertIsNotNone(get_form(RequestFactory().post("/", {"field": "value"}), forms.Form))
