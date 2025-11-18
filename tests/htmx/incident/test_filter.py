from unittest.mock import Mock

from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import QueryDict
from django.test import RequestFactory, TestCase
import json

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.htmx.incident.filter import IncidentFilterForm, NamedFilterForm, create_named_filter, incident_list_filter
from argus.htmx.incident.views import search_tags
from argus.incident.constants import AckedStatus, OpenStatus
from argus.incident.factories import IncidentFactory, SourceSystemFactory
from argus.incident.models import Incident, Tag
from argus.notificationprofile.models import Filter
from argus.util.testing import connect_signals, disconnect_signals


class TestIncidentFilterForm(TestCase):
    def setUp(self) -> None:
        disconnect_signals()
        source = SourceSystemFactory(name="testsource")
        self.valid_field_values = {
            "open": OpenStatus.OPEN,
            "acked": AckedStatus.ACKED,
            "sourceSystemIds": [source.id],
            "tags": ["tag1=value1", "tag2=value2"],
            "maxlevel": 1,
        }
        self.valid_form = IncidentFilterForm(self.valid_field_values)

    def teardown(self):
        connect_signals()

    def test_if_form_is_valid_then_filterblob_should_contain_correct_open_value(self):
        filterblob = self.valid_form.to_filterblob()
        assert filterblob["open"] is True

    def test_if_form_is_valid_then_filterblob_should_contain_correct_acked_value(self):
        filterblob = self.valid_form.to_filterblob()
        print("Filterblob")
        assert filterblob["acked"] is True

    def test_if_form_is_valid_then_filterblob_should_contain_correct_sourcesystemids_value(self):
        filterblob = self.valid_form.to_filterblob()
        assert len(filterblob["sourceSystemIds"]) == 1
        # sourceSystemIds seem to be represented as a list of strings sometimes
        assert int(filterblob["sourceSystemIds"][0]) == int(self.valid_field_values["sourceSystemIds"][0])

    def test_if_form_is_valid_then_filterblob_should_contain_correct_tags_value(self):
        filterblob = self.valid_form.to_filterblob()
        assert filterblob["tags"] == self.valid_field_values["tags"]

    def test_if_form_is_not_valid_then_to_filterblob_should_return_an_empty_dict(self):
        form = IncidentFilterForm({"tags": "invalidtags"})
        filterblob = form.to_filterblob()
        assert filterblob == {}

    def test_lack_of_tags_should_not_cause_an_error(self):
        """Tests clean_tags via is_valid"""
        form = IncidentFilterForm({})
        assert form.is_valid()
        assert "tags" not in form.errors

    def test_if_tags_have_wrong_format_then_it_should_create_an_error(self):
        """Tests clean_tags via is_valid"""
        form = IncidentFilterForm({"tags": "invalidtags"})
        assert not form.is_valid()
        assert "tags" in form.errors


class TestIncidentListFilter(TestCase):
    def setUp(self) -> None:
        disconnect_signals()
        self.source = SourceSystemFactory(name="testsource")
        self.incident = IncidentFactory(level=5, source=self.source)
        self.qs = Incident.objects.filter(source=self.source)
        self.factory = RequestFactory()
        self.request = self.factory.get("/random-url")
        self.request.user = PersonUserFactory()
        self.valid_filter = FilterFactory(
            filter={
                "open": True,
                "acked": True,
                "maxlevel": 1,
                "tags": [],
            }
        )
        self.invalid_filter = FilterFactory(
            filter={
                "tags": ["invalidtags"],
            }
        )

        SessionMiddleware(lambda x: x).process_request(self.request)
        MessageMiddleware(lambda x: x).process_request(self.request)

    def teardown(self):
        connect_signals()

    def test_valid_request_should_return_filtered_queryset(self):
        self.request.session["selected_filter"] = self.valid_filter.pk
        _, qs = incident_list_filter(self.request, self.qs)
        assert self.incident in self.qs
        assert self.incident not in qs

    def test_invalid_request_should_return_unfiltered_queryset(self):
        self.request.session["selected_filter"] = self.invalid_filter.pk
        _, qs = incident_list_filter(self.request, self.qs)
        assert qs == self.qs

    def test_valid_request_should_return_form_with_correct_values(self):
        self.request.session["selected_filter"] = self.valid_filter.pk
        form, _ = incident_list_filter(self.request, self.qs)
        assert form.to_filterblob()["maxlevel"] == self.valid_filter.filter["maxlevel"]

    def test_invalid_request_should_return_form_with_errors(self):
        self.request.session["selected_filter"] = self.invalid_filter.pk
        form, _ = incident_list_filter(self.request, self.qs)
        assert form.errors

    def test_get_request_without_selected_filter_should_use_get_parameters_as_form_data(self):
        maxlevel = 3
        self.request.session["selected_filter"] = None
        self.request.GET = QueryDict(f"tags=&maxlevel={maxlevel}")
        form, _ = incident_list_filter(self.request, self.qs)
        assert form.to_filterblob()["maxlevel"] == maxlevel

    def test_post_request_without_selected_filter_should_use_post_parameters_as_form_data(self):
        maxlevel = 3
        request = self.factory.post("random-url", {}, content_type="application/json")
        request.POST = QueryDict(f"tags=&maxlevel={maxlevel}")
        SessionMiddleware(lambda x: x).process_request(request)
        MessageMiddleware(lambda x: x).process_request(request)
        form, _ = incident_list_filter(request, self.qs)
        assert form.to_filterblob()["maxlevel"] == maxlevel


class TestCreateNamedFilter(TestCase):
    def setUp(self) -> None:
        disconnect_signals()
        self.request = Mock()
        self.request.user = PersonUserFactory()
        self.filterblob = {
            "open": True,
            "acked": True,
        }

    def teardown(self):
        connect_signals()

    def test_if_input_is_valid_it_should_return_a_filter(self):
        filter_name = "myfilter"
        _, filter_obj = create_named_filter(self.request, filter_name, self.filterblob)
        assert isinstance(filter_obj, Filter)

    def test_if_input_is_invalid_it_should_not_return_a_filter(self):
        invalid_name = ""
        _, filter_obj = create_named_filter(self.request, invalid_name, self.filterblob)
        assert not filter_obj

    def test_should_return_a_named_filter_form(self):
        filter_name = "myfilter"
        form, _ = create_named_filter(self.request, filter_name, self.filterblob)
        assert isinstance(form, NamedFilterForm)


class TestSearchTagsFilter(TestCase):
    def setUp(self) -> None:
        disconnect_signals()
        self.factory = RequestFactory()

    def tearDown(self):
        connect_signals()

    def test_search_tags_without_query_returns_empty_results(self):
        request = self.factory.get("/search-tags/")
        response = search_tags(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data == {"results": []}

    def test_search_tags_with_key_value_query_filters_by_key_and_value(self):
        # Create test tags
        tag1 = Tag.objects.create(key="environment", value="production")
        _tag2 = Tag.objects.create(key="environment", value="staging")
        _tag3 = Tag.objects.create(key="service", value="api")

        query = f"environment{Tag.TAG_DELIMITER}prod"
        request = self.factory.get("/search-tags/", {"q": query})
        response = search_tags(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == str(tag1)
        assert data["results"][0]["text"] == str(tag1)

    def test_search_tags_with_key_only_query_filters_by_key(self):
        from argus.incident.models import Tag

        # Create test tags
        tag1 = Tag.objects.create(key="environment", value="production")
        tag2 = Tag.objects.create(key="environment", value="staging")
        _tag3 = Tag.objects.create(key="service", value="api")

        request = self.factory.get("/search-tags/", {"q": "env"})
        response = search_tags(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data["results"]) == 2
        tag_ids = [result["id"] for result in data["results"]]
        assert str(tag1) in tag_ids
        assert str(tag2) in tag_ids

    def test_search_tags_limits_results_to_20(self):
        from argus.incident.models import Tag

        # Create 25 test tags
        for i in range(25):
            Tag.objects.create(key=f"test{i}", value="value")

        request = self.factory.get("/search-tags/", {"q": "test"})
        response = search_tags(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data["results"]) == 20

    def test_search_tags_returns_correct_json_format(self):
        from argus.incident.models import Tag

        tag = Tag.objects.create(key="service", value="web")
        request = self.factory.get("/search-tags/", {"q": "service"})
        response = search_tags(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert "results" in data
        assert len(data["results"]) == 1
        result = data["results"][0]
        assert "id" in result
        assert "text" in result
        assert result["id"] == str(tag)
        assert result["text"] == str(tag)
