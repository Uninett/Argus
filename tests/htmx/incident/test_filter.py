import json
from unittest.mock import Mock

from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404, QueryDict
from django.test import RequestFactory, TestCase

from argus.auth.factories import PersonUserFactory
from argus.auth.utils import get_preference_obj
from argus.filter.factories import FilterFactory
from argus.htmx.incident.filter import IncidentFilterForm, NamedFilterForm, create_named_filter, incident_list_filter
from argus.htmx.incident.views import create_filter, update_filter, delete_filter, search_tags
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
            "source_types": [source.type.name],
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
        assert filterblob["acked"] is True

    def test_if_form_is_valid_then_filterblob_should_contain_correct_sourcesystemids_value(self):
        filterblob = self.valid_form.to_filterblob()
        assert len(filterblob["sourceSystemIds"]) == 1
        # sourceSystemIds seem to be represented as a list of strings sometimes
        assert int(filterblob["sourceSystemIds"][0]) == int(self.valid_field_values["sourceSystemIds"][0])

    def test_if_form_is_valid_then_filterblob_should_contain_correct_sourcesystem_types_value(self):
        filterblob = self.valid_form.to_filterblob()
        assert len(filterblob["source_types"]) == 1

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

    def test_nonexistent_filter_should_return_unfiltered_queryset_and_repair_session(self):
        self.request.session["selected_filter"] = -1
        _, qs = incident_list_filter(self.request, self.qs)
        self.assertEqual(qs, self.qs)
        self.assertNotIn("selected_filter", self.request.session)

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


class TestFilterPreference(TestCase):
    def setUp(self):
        disconnect_signals()
        self.source = SourceSystemFactory(name="testsource")
        self.qs = Incident.objects.filter(source=self.source)
        self.factory = RequestFactory()
        self.user = PersonUserFactory()

    def tearDown(self):
        connect_signals()

    def _setup_request(self, request):
        request.user = self.user
        SessionMiddleware(lambda x: x).process_request(request)
        MessageMiddleware(lambda x: x).process_request(request)
        request.session["selected_filter"] = None

    def test_use_empty_filter_uses_default_values(self):
        """use_empty_filter=True should use DEFAULT_VALUES"""
        request = self.factory.get("/incidents/")
        self._setup_request(request)

        form, _ = incident_list_filter(request, self.qs, use_empty_filter=True)

        assert form.is_valid()
        filterblob = form.to_filterblob()
        assert filterblob.get("maxlevel") == IncidentFilterForm.DEFAULT_VALUES["maxlevel"]

    def test_stored_preference_is_loaded_when_no_url_params(self):
        """When no URL filter params, stored preference should be loaded"""
        request = self.factory.get("/incidents/")
        self._setup_request(request)

        # Store a preference
        prefs = get_preference_obj(request, "argus_htmx")
        prefs.save_preference("incident_filter", {"maxlevel": 2, "open": True, "acked": None})

        form, _ = incident_list_filter(request, self.qs)

        assert form.to_filterblob().get("maxlevel") == 2

    def test_empty_form_when_no_preference_and_no_url_params(self):
        """When no stored preference and no URL params, unbound empty form is used"""
        request = self.factory.get("/incidents/")
        self._setup_request(request)

        # Ensure no preference is stored
        prefs = get_preference_obj(request, "argus_htmx")
        prefs.save_preference("incident_filter", {})

        form, _ = incident_list_filter(request, self.qs)

        # An unbound form (None passed to constructor) is not bound
        assert not form.is_bound

    def test_invalid_form_with_get_params_shows_error_messages(self):
        """Invalid filter with GET params should add error messages"""
        request = self.factory.get("/incidents/", {"tags": "invalid-no-equals"})
        self._setup_request(request)

        form, _ = incident_list_filter(request, self.qs)

        assert not form.is_valid()
        assert "tags" in form.errors


class TestCreateFilterView(TestCase):
    def setUp(self):
        disconnect_signals()
        self.factory = RequestFactory()
        self.user = PersonUserFactory()

    def tearDown(self):
        connect_signals()

    def _post(self, data, selected_filter=None):
        request = self.factory.post("/filter-create/", data)
        request.user = self.user
        SessionMiddleware(lambda x: x).process_request(request)
        MessageMiddleware(lambda x: x).process_request(request)
        if selected_filter:
            request.session["selected_filter"] = selected_filter
        return create_filter(request)

    def test_when_valid_then_it_should_create_filter_and_return_refresh(self):
        response = self._post({"filter_name": "My filter", "maxlevel": 5, "tags": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Filter.objects.filter(name="My filter", user=self.user).exists())

    def test_when_session_has_selected_filter_then_it_should_use_post_data(self):
        existing = FilterFactory(user=self.user, filter={"maxlevel": 1, "tags": []})
        response = self._post(
            {"filter_name": "New filter", "maxlevel": 3, "tags": ""},
            selected_filter=str(existing.pk),
        )
        self.assertEqual(response.status_code, 200)
        new_filter = Filter.objects.get(name="New filter", user=self.user)
        self.assertEqual(new_filter.filter["maxlevel"], 3)

    def test_when_name_missing_then_it_should_return_bad_request(self):
        response = self._post({"maxlevel": 5, "tags": ""})
        self.assertEqual(response.status_code, 400)

    def test_when_session_has_selected_filter_then_it_should_preserve_session(self):
        existing = FilterFactory(user=self.user, filter={"maxlevel": 1, "tags": []})
        request = self.factory.post("/filter-create/", {"filter_name": "test", "maxlevel": 5, "tags": ""})
        request.user = self.user
        SessionMiddleware(lambda x: x).process_request(request)
        MessageMiddleware(lambda x: x).process_request(request)
        request.session["selected_filter"] = str(existing.pk)
        create_filter(request)
        self.assertIsNotNone(request.session.get("selected_filter"))


class TestUpdateFilterView(TestCase):
    def setUp(self):
        disconnect_signals()
        self.factory = RequestFactory()
        self.user = PersonUserFactory()
        self.filter_obj = FilterFactory(user=self.user, name="Original", filter={"maxlevel": 1, "tags": []})

    def tearDown(self):
        connect_signals()

    def _post(self, pk, data, user=None, selected_filter=None):
        request = self.factory.post(f"/filter/update/{pk}/", data)
        request.user = user or self.user
        SessionMiddleware(lambda x: x).process_request(request)
        MessageMiddleware(lambda x: x).process_request(request)
        if selected_filter:
            request.session["selected_filter"] = selected_filter
        return update_filter(request, pk)

    def test_when_valid_then_it_should_update_filter_and_return_refresh(self):
        response = self._post(self.filter_obj.pk, {"maxlevel": 3, "tags": ""})
        self.assertEqual(response.status_code, 200)
        self.filter_obj.refresh_from_db()
        self.assertEqual(self.filter_obj.filter["maxlevel"], 3)

    def test_when_session_has_selected_filter_then_it_should_use_post_data(self):
        other_filter = FilterFactory(user=self.user, filter={"maxlevel": 5, "tags": []})
        response = self._post(
            self.filter_obj.pk,
            {"maxlevel": 2, "tags": ""},
            selected_filter=str(other_filter.pk),
        )
        self.assertEqual(response.status_code, 200)
        self.filter_obj.refresh_from_db()
        self.assertEqual(self.filter_obj.filter["maxlevel"], 2)

    def test_when_other_user_then_it_should_return_forbidden(self):
        other_user = PersonUserFactory()
        response = self._post(self.filter_obj.pk, {"maxlevel": 3, "tags": ""}, user=other_user)
        self.assertEqual(response.status_code, 403)

    def test_when_filter_not_found_then_it_should_raise_404(self):
        with self.assertRaises(Http404):
            self._post(99999, {"maxlevel": 3, "tags": ""})


class TestDeleteFilterView(TestCase):
    def setUp(self):
        disconnect_signals()
        self.factory = RequestFactory()
        self.user = PersonUserFactory()
        self.filter_obj = FilterFactory(user=self.user, name="To delete", filter={})

    def tearDown(self):
        connect_signals()

    def _post(self, pk, user=None, selected_filter=None):
        request = self.factory.post(f"/filter/delete/{pk}/")
        request.user = user or self.user
        SessionMiddleware(lambda x: x).process_request(request)
        MessageMiddleware(lambda x: x).process_request(request)
        if selected_filter:
            request.session["selected_filter"] = selected_filter
        return delete_filter(request, pk), request

    def test_when_valid_then_it_should_delete_filter_and_return_refresh(self):
        pk = self.filter_obj.pk
        response, _ = self._post(pk)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Filter.objects.filter(pk=pk).exists())

    def test_when_deleted_filter_was_selected_then_it_should_clear_session(self):
        pk = self.filter_obj.pk
        _, request = self._post(pk, selected_filter=str(pk))
        self.assertIsNone(request.session.get("selected_filter"))

    def test_when_other_user_then_it_should_return_forbidden(self):
        other_user = PersonUserFactory()
        response, _ = self._post(self.filter_obj.pk, user=other_user)
        self.assertEqual(response.status_code, 403)

    def test_when_filter_not_found_then_it_should_raise_404(self):
        with self.assertRaises(Http404):
            self._post(99999)


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
