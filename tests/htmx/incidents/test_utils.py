from unittest.mock import Mock

from django import test
from django.http import HttpResponseRedirect
from django.test.client import RequestFactory

from argus.htmx.incidents.filter import incident_list_filter
from argus.htmx.incidents.utils import get_filter_function
from argus.htmx.middleware import LoginRequiredMiddleware


class TestGetFilterFunction(test.TestCase):
    def test_gets_incident_list_filter_by_default(self):
        self.assertIs(get_filter_function(), incident_list_filter)

    def test_gets_callable_directly(self):
        sentinel = object
        self.assertIs(get_filter_function(sentinel), sentinel)

    def test_gets_incident_list_filter_from_dotted_path(self):
        self.assertIs(
            get_filter_function("argus.htmx.incidents.filter.incident_list_filter"),
            incident_list_filter,
        )

    def test_gets_incident_list_filter_from_module(self):
        self.assertIs(get_filter_function("argus.htmx.incidents.filter"), incident_list_filter)
