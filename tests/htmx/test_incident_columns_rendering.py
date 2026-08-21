from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django import forms, test
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.filter.queryset_filters import QuerySetFilter
from argus.htmx.incident.columns import IncidentTableColumn
from argus.htmx.incident.views import (
    filter_form as filter_form_view,
    filter_select,
    get_form,
    get_incident_ids_to_update,
    incident_list,
    incident_list_kiosk,
    KIOSK_URL_NAME,
)
from argus.htmx.user.factories import ArgusHtmxPreferencesFactory
from argus.htmx.user.preferences.models import ArgusHtmxPreferences
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
        self.assertNotContains(self.kiosk_response, "Sort by")
        self.assertNotContains(self.kiosk_response, "filter-btn")

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

    def test_given_kiosk_mode_with_selected_filter_it_should_display_filter_name(self):
        filter_obj = FilterFactory(user=self.user, name="Kiosk Test Filter XYZ")
        request = RequestFactory().get("/incidents/kiosk/")
        request.session = {"selected_filter": str(filter_obj.pk)}
        request.user = self.user
        request.htmx = False
        response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, "Kiosk Test Filter XYZ")

    def test_given_kiosk_mode_with_selected_filter_and_matching_url_it_should_display_filter_name(self):
        filter_obj = FilterFactory(user=self.user, name="Kiosk Test Filter XYZ", filter={"maxlevel": 1})
        request = RequestFactory().get("/incidents/kiosk/", {"maxlevel": "1"})
        request.session = {"selected_filter": str(filter_obj.pk)}
        request.user = self.user
        request.htmx = False
        response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, "Kiosk Test Filter XYZ")

    def test_given_kiosk_mode_with_selected_filter_and_unsaved_edits_it_should_display_unsaved(self):
        filter_obj = FilterFactory(user=self.user, name="Kiosk Test Filter XYZ", filter={"maxlevel": 1})
        request = RequestFactory().get("/incidents/kiosk/", {"maxlevel": "3"})
        request.session = {"selected_filter": str(filter_obj.pk)}
        request.user = self.user
        request.htmx = False
        response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, "Unsaved")
        self.assertNotContains(response, "Kiosk Test Filter XYZ")

    def test_given_kiosk_mode_with_no_filter_at_all_it_should_display_unset(self):
        self.assertContains(self.kiosk_response, "Unset")

    def test_given_kiosk_mode_with_ad_hoc_filter_params_it_should_display_unsaved(self):
        request = RequestFactory().get("/incidents/kiosk/", {"maxlevel": "1"})
        request.session = {}
        request.user = self.user
        request.htmx = False
        response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, "Unsaved")

    def test_given_kiosk_mode_with_stored_preference_it_should_display_unsaved(self):
        preferences = ArgusHtmxPreferences.objects.get(user=self.user, namespace="argus_htmx")
        preferences.preferences["incident_filter"] = {"maxlevel": 1}
        preferences.save()
        request = RequestFactory().get("/incidents/kiosk/")
        request.session = {}
        request.user = self.user
        request.htmx = False
        response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, "Unsaved")

    def test_given_kiosk_mode_it_should_keep_filterbox_values_for_autorefresh(self):
        self.assertContains(self.kiosk_response, 'id="incident-filter-box"')
        self.assertNotContains(self.kiosk_response, "load once")

    @test.override_settings(INCIDENT_TABLE_COLUMNS=["row_select", "search_id"])
    def test_given_kiosk_mode_it_should_keep_column_filter_values_for_autorefresh(self):
        request = RequestFactory().get("/incidents/kiosk/", {"id": "42"})
        request.session = {}
        request.user = self.user
        request.htmx = False
        response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, 'class="incident-list-param flex-1 peer"')
        self.assertContains(response, 'value="42"')
        self.assertNotContains(response, 'id="search_id-dropdown"')

    def test_given_kiosk_mode_with_a_page_number_above_1_it_should_reset_to_page_1(self):
        def unfiltered_incident_list_filter(request, qs):
            return forms.Form(), qs

        StatelessIncidentFactory.create_batch(6)
        # Patch so that 3 is a valid page size
        with patch("argus.htmx.incident.views.KIOSK_PAGE_SIZE", 2):
            with test.override_settings(ARGUS_HTMX_FILTER_FUNCTION=unfiltered_incident_list_filter):
                request = RequestFactory().get("/incidents/kiosk/", {"page": "3"})
                request.session = {}
                request.user = self.user
                request.htmx = False
                response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, 'hx-vals=\'{"page": "1"')

    def test_given_kiosk_mode_with_default_stored_preference_it_should_display_unset(self):
        preferences = ArgusHtmxPreferences.objects.get(user=self.user, namespace="argus_htmx")
        preferences.preferences["incident_filter"] = {"open": None, "acked": None, "maxlevel": 5}
        preferences.save()
        request = RequestFactory().get("/incidents/kiosk/")
        request.session = {}
        request.user = self.user
        request.htmx = False
        response = incident_list(request, kiosk_mode=True)
        self.assertContains(response, "Unset")


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
        now = timezone.now()
        older = StatelessIncidentFactory(level=3, start_time=now - timedelta(hours=2))
        newer = StatelessIncidentFactory(level=3, start_time=now - timedelta(hours=1))
        response = incident_list(self._make_request({"sort": "level", "maxlevel": 5}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertLess(
            content.index(f'id="incident-{newer.pk}-row"'),
            content.index(f'id="incident-{older.pk}-row"'),
        )

    def test_given_timeframe_in_session_it_should_include_timeframe_in_query(self):
        now = timezone.now()
        within_timeframe = StatelessIncidentFactory(start_time=now - timedelta(minutes=10))
        outside_timeframe = StatelessIncidentFactory(start_time=now - timedelta(minutes=120))
        request = self._make_request()
        request.session["timeframe"] = 60
        response = incident_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'id="incident-{within_timeframe.pk}-row"')
        self.assertNotContains(response, f'id="incident-{outside_timeframe.pk}-row"')


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
