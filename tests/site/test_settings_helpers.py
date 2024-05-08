import unittest
from copy import deepcopy

from django.conf import settings
from django.urls.resolvers import URLResolver
from django.test import override_settings

from argus.site.settings import normalize_url, _add_missing_scheme_to_url
from argus.site.settings._serializers import AppSetting
from argus.site.utils import get_urlpatterns_from_setting, update_context_processors_list


class NormalizeUrlTests(unittest.TestCase):
    def test_add_missing_scheme_if_recoverable(self):
        test_url_80 = "//localhost:80/fgh/ghj/?ghj=gh#fghj"
        fixed_url = _add_missing_scheme_to_url(test_url_80)
        correct_url_80 = "http://localhost:80/fgh/ghj/?ghj=gh#fghj"
        self.assertEqual(fixed_url, correct_url_80)
        test_url_443 = "//localhost:443/fgh/ghj/?ghj=gh#fghj"
        fixed_url = _add_missing_scheme_to_url(test_url_443)
        correct_url_443 = "https://localhost:443/fgh/ghj/?ghj=gh#fghj"
        self.assertEqual(fixed_url, correct_url_443)

    def test_dont_add_missing_scheme_if_not_recoverable(self):
        test_url_noport = "//localhost/fgh/ghj/?ghj=gh#fghj"
        fixed_url = _add_missing_scheme_to_url(test_url_noport)
        self.assertEqual(fixed_url, test_url_noport)
        test_url_unknown_port = "//localhost:5431/fgh/ghj/?ghj=gh#fghj"
        fixed_url = _add_missing_scheme_to_url(test_url_unknown_port)
        self.assertEqual(fixed_url, test_url_unknown_port)

    def test_strip_redundant_ports(self):
        test_url_80 = "http://localhost:80/fgh/ghj/?ghj=gh#fghj"
        fixed_url = normalize_url(test_url_80)
        correct_url_80 = "http://localhost/fgh/ghj/?ghj=gh#fghj"
        self.assertEqual(fixed_url, correct_url_80)
        test_url_443 = "https://localhost:443/fgh/ghj/?ghj=gh#fghj"
        fixed_url = normalize_url(test_url_443)
        correct_url_443 = "https://localhost/fgh/ghj/?ghj=gh#fghj"
        self.assertEqual(fixed_url, correct_url_443)

    def test_dont_strip_unknown_ports(self):
        test_url_unknown_port = "http://localhost:5431/fgh/ghj/?ghj=gh#fghj"
        fixed_url = normalize_url(test_url_unknown_port)
        self.assertEqual(fixed_url, test_url_unknown_port)


class GetUrlPatternsFromSettingsTest(unittest.TestCase):
    def test_if_falsey_setting_return_empty_list(self):
        self.assertEqual(get_urlpatterns_from_setting(None), [])

    def test_if_falsey_urls_return_empty_list(self):
        class Obj:
            pass

        obj = Obj()
        obj.urls = None

        self.assertEqual(get_urlpatterns_from_setting([obj]), [])

    def test_urls_without_namspace_return_list_of_paths_without_namespace(self):
        raw_setting = {
            "app_name": "foo",
            "urls": {
                "path": "fghfh",
                "urlpatterns_module": "django",  # must be a dotted path to a module in python path!
            },
        }
        setting = AppSetting(**raw_setting)
        result = get_urlpatterns_from_setting([setting])
        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result[0], URLResolver))
        self.assertFalse(result[0].namespace)

    def test_urls_with_namspace_return_list_of_paths_with_namespace(self):
        raw_setting = {
            "app_name": "foo",
            "urls": {
                "path": "fghfh",
                "urlpatterns_module": "django",  # must be a dotted path to a module in python path!
                "namespace": "blbl",
            },
        }
        setting = AppSetting(**raw_setting)
        result = get_urlpatterns_from_setting([setting])
        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result[0], URLResolver))
        self.assertEqual(result[0].namespace, "blbl")


class UpdateContextProcessorsListTests(unittest.TestCase):
    def test_do_nothing_if_empty_list(self):
        old_setting = deepcopy(settings.TEMPLATES)
        result = update_context_processors_list([])
        self.assertTrue(result)
        new_setting = deepcopy(settings.TEMPLATES)
        self.assertEqual(old_setting, new_setting)

    @override_settings(TEMPLATES=[{"BACKEND": "foo", "OPTIONS": {"context_processors": ["alpha"]}}])
    def test_only_update_DjangoTemplates_section(self):
        old_setting = deepcopy(settings.TEMPLATES)[0]
        result = update_context_processors_list(["omega"])
        self.assertFalse(result)
        new_setting = deepcopy(settings.TEMPLATES[0])
        self.assertEqual(old_setting, new_setting)

    @override_settings(TEMPLATES=[])
    def test_return_None_if_no_setting(self):
        result = update_context_processors_list(["n"])
        self.assertEqual(result, None)

    def test_append_list_to_DjangoTemplates_context_processors(self):
        old_setting = deepcopy(settings.TEMPLATES[0])
        new_cps = ["a", "b"]
        result = update_context_processors_list(new_cps)
        self.assertTrue(result)
        new_setting = deepcopy(settings.TEMPLATES[0])
        self.assertNotEqual(old_setting, new_setting)
        old_cps = old_setting["OPTIONS"].pop("context_processors")
        new_cps = new_setting["OPTIONS"].pop("context_processors")
        self.assertEqual(old_setting, new_setting)
        self.assertNotEqual(old_cps, new_cps)
