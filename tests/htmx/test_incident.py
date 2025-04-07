from django import forms, test
from django.test.client import RequestFactory
from argus.auth.factories import PersonUserFactory
from argus.filter.queryset_filters import QuerySetFilter
from argus.htmx.incident.customization import IncidentTableColumn
from argus.htmx.incident.views import incident_list


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
        self.response = incident_list(request)

    def test_doesnt_add_filter_button_to_header(self):
        self.assertNotContains(self.response, '_="on click toggle .hidden on next .column-filter"')

    def test_add_filter_to_filterbox(self):
        self.assertContains(self.response, '<span class="label-text">Description</span>')


@test.override_settings(
    ARGUS_HTMX_FILTER_FUNCTION=incident_list_filter_factory(IncidentColumnFilterForm),
    INCIDENT_TABLE_COLUMNS=[
        IncidentTableColumn(
            "description",
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
        self.response = incident_list(request)

    def test_adds_filter_button_to_header(self):
        self.assertContains(self.response, '_="on click toggle .hidden on next .column-filter"')

    def test_doesnt_add_filter_to_filterbox(self):
        self.assertNotContains(self.response, '<span class="label-text">Description</span>')
