from django import test

from argus.htmx.incidents.utils import get_filter_function


class TestGetFilterFunction(test.TestCase):
    def setUp(self) -> None:
        from argus.htmx.incidents.filter import incident_list_filter

        self.incident_list_filter = incident_list_filter

    def test_gets_incident_list_filter_by_default(self):
        self.assertIs(get_filter_function(), self.incident_list_filter)

    def test_gets_callable_directly(self):
        sentinel = object
        self.assertIs(get_filter_function(sentinel), sentinel)

    def test_gets_incident_list_filter_from_dotted_path(self):
        self.assertIs(
            get_filter_function("argus.htmx.incidents.filter.incident_list_filter"),
            self.incident_list_filter,
        )

    def test_gets_incident_list_filter_from_module(self):
        self.assertIs(
            get_filter_function("argus.htmx.incidents.filter"),
            self.incident_list_filter,
        )
