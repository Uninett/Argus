from django import test

from argus.htmx.incident.utils import get_filter_function


class TestGetFilterFunction(test.TestCase):
    def setUp(self) -> None:
        # importing incident_list_filter requires a fully migrated database. During tests,
        # especially in CI, this cannot be guaranteed if we import incident_list_filter at the
        # top of this file. So we postpone importing until the tests are run.
        from argus.htmx.incident.filter import incident_list_filter

        self.incident_list_filter = incident_list_filter

    def test_gets_incident_list_filter_by_default(self):
        self.assertIs(get_filter_function(), self.incident_list_filter)

    def test_gets_callable_directly(self):
        sentinel = object
        self.assertIs(get_filter_function(sentinel), sentinel)

    def test_gets_incident_list_filter_from_dotted_path(self):
        self.assertIs(
            get_filter_function("argus.htmx.incident.filter.incident_list_filter"),
            self.incident_list_filter,
        )

    def test_gets_incident_list_filter_from_module(self):
        self.assertIs(
            get_filter_function("argus.htmx.incident.filter"),
            self.incident_list_filter,
        )
