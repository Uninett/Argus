from django.test import override_settings, TestCase

from argus.filter import get_filter_backend


class GetFilterBackendTest(TestCase):
    def test_get_filter_backend_returns_default_backend_if_setting_not_set(self):
        filter_backend = get_filter_backend()
        self.assertFalse(hasattr(filter_backend, "DummyClass"), "filter backend is not the default backend")
        self.assertEqual(filter_backend.__name__, "argus.filter.default")

    @override_settings(ARGUS_FILTER_BACKEND="tests.filter.dummyplugin")
    def test_get_filter_backend_returns_the_right_format_module(self):
        filter_backend = get_filter_backend()
        self.assertTrue(hasattr(filter_backend, "DummyClass"), "filter backend is not the dummy backend")
        self.assertEqual(filter_backend.__name__, "tests.filter.dummyplugin")
