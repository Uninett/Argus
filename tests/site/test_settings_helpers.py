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
    def test_when_setting_is_falsey_return_empty_list(self):
        self.assertEqual(get_urlpatterns_from_setting(None), [])

    def test_when_setting_urls_is_falsey_it_should_return_empty_list(self):
        class Obj:
            pass

        obj = Obj()
        obj.urls = None

        self.assertEqual(get_urlpatterns_from_setting([obj]), [])

    def test_urls_without_namespace_return_list_of_paths_without_namespace(self):
        # django.urls.include has one obligatory positional argument that is
        # either an urlpatterns-list or a dotted path to a module that contains
        # an urlpatterns list that is labeled "urlpatterns". It also has
        # a keyword argument "namespace". This tests including urlpatterns that
        # DOES NOT have namespace set.
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

    def test_urls_with_namespace_return_list_of_paths_with_namespace(self):
        # django.urls.include has one obligatory positional argument that is
        # either an urlpatterns-list or a dotted path to a module that contains
        # an urlpatterns list that is labeled "urlpatterns". It also has
        # a keyword argument "namespace". This tests including urlpatterns that
        # DO have namespace set.
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
    def test_when_context_processor_setting_is_unset_it_should_do_nothing(self):
        raw_setting = {
            "app_name": "foo",
            "urls": {
                "path": "fghfh",
                "urlpatterns_module": "django",  # must be a dotted path to a module in python path!
                "namespace": "blbl",
            },
            # NO "context_processors"-key!
        }
        TEMPLATES = []
        result = update_context_processors_list(TEMPLATES, None)
        self.assertEqual(result, TEMPLATES)

    def test_when_template_setting_is_falsey_it_should_do_nothing(self):
        TEMPLATES = []
        raw_setting = {
            "app_name": "foo",
            "context_processors": ["omega"],
        }
        app_setting = AppSetting(**raw_setting)
        result = update_context_processors_list(TEMPLATES, [app_setting])
        self.assertEqual(result, TEMPLATES)

    def test_when_it_is_not_a_DjangoTemplates_section_it_should_do_nothing(self):
        raw_setting = {
            "app_name": "foo",
            "context_processors": ["omega"],
        }
        app_setting = AppSetting(**raw_setting)
        TEMPLATES = [
            {"BACKEND": "django.template.backends.jinja2.Jinja2", "OPTIONS": {"context_processors": ["alpha"]}}
        ]
        result = update_context_processors_list(TEMPLATES, [app_setting])
        self.assertEqual(result, TEMPLATES)

    def test_when_app_settings_contain_context_processors_it_should_append_them_to_DjangoTemplates_context_processors_list(
        self,
    ):
        raw_setting = {
            "app_name": "foo",
            "context_processors": ["omega"],
        }
        app_setting = AppSetting(**raw_setting)
        TEMPLATES = [
            {"BACKEND": "django.template.backends.django.DjangoTemplates", "OPTIONS": {"context_processors": ["alpha"]}}
        ]
        result = update_context_processors_list(TEMPLATES, [app_setting])
        self.assertTrue(result)
        self.assertNotEqual(TEMPLATES, result)
        old_cps = TEMPLATES[0]["OPTIONS"].pop("context_processors")
        new_cps = result[0]["OPTIONS"].pop("context_processors")
        self.assertEqual(TEMPLATES, result)
        self.assertNotEqual(old_cps, new_cps)
        self.assertEqual(new_cps, ["alpha", "omega"])
