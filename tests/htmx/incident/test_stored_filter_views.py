from django.http.response import Http404
from django.test import tag, RequestFactory, TestCase

from argus.htmx.incident.views import filter_select
from argus.filter.factories import FilterFactory


class Dummy:
    pass


class filter_select_Test(TestCase):
    factory = RequestFactory()

    @tag("unit")
    def test_when_no_filter_in_request_should_unset_filter_in_session(self):
        request = self.factory.get("")
        request.session = dict()
        request.htmx = Dummy()
        request.htmx.trigger = None

        response = filter_select(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Retarget", response.headers)
        self.assertIsNone(request.session["selected_filter_pk"])
        self.assertNotIn("selected_filter_name", request.session)

    def test_when_valid_filter_in_request_set_filter_in_session(self):
        filter_ = FilterFactory()
        request = self.factory.get(f"?filter={filter_.pk}")
        request.session = dict()
        request.htmx = Dummy()
        request.htmx.trigger = None

        response = filter_select(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Retarget", response.headers)
        self.assertEqual(request.session["selected_filter_pk"], str(filter_.pk))
        self.assertEqual(request.session["selected_filter_name"], filter_.name)

    def test_when_valid_filter_in_request_and_htmx_return_page(self):
        filter_ = FilterFactory()
        request = self.factory.get(f"?filter={filter_.pk}")
        request.session = dict()
        request.htmx = Dummy()
        request.htmx.trigger = True
        request.user = filter_.user

        response = filter_select(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Retarget", response.headers)
        self.assertIn(filter_.name, response.text)

    def test_when_invalid_filter_in_request_raise_404(self):
        filter_ = FilterFactory()
        pk = filter_.pk + 100
        request = self.factory.get(f"?filter={pk}")

        with self.assertRaises(Http404):
            filter_select(request)
