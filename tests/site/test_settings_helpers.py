import unittest
from urllib.parse import urljoin

from django.urls.resolvers import URLResolver

from argus.site.settings import (
    append_suburl,
    normalize_url,
    normalize_suburl,
    prefix_relative_url,
    _add_missing_scheme_to_url,
)
from argus.site.settings._serializers import AppSetting
from argus.site.utils import get_urlpatterns, update_context_processors_list


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


class NormalizeSuburlTests(unittest.TestCase):
    def test_given_any_spelling_of_a_suburl_it_should_normalize_to_the_path_form(self):
        # django.urls.path() only ever matches this one form: no leading
        # slash, exactly one trailing slash
        for spelling in ("argus", "/argus", "argus/", "/argus/"):
            with self.subTest(spelling=spelling):
                self.assertEqual(normalize_suburl(spelling), "argus/")

    def test_given_a_suburl_with_surrounding_whitespace_it_should_be_stripped(self):
        self.assertEqual(normalize_suburl("  /argus/  "), "argus/")

    def test_given_a_multi_segment_suburl_it_should_keep_every_segment(self):
        self.assertEqual(normalize_suburl("/tools/argus"), "tools/argus/")

    def test_given_repeated_slashes_it_should_collapse_them(self):
        # path() would otherwise demand a literal "//" in the url to match
        self.assertEqual(normalize_suburl("//tools//argus//"), "tools/argus/")

    def test_given_an_empty_suburl_it_should_stay_empty(self):
        # an empty suburl means "serve from the domain root"
        for spelling in ("", "/", "  ", "///"):
            with self.subTest(spelling=spelling):
                self.assertEqual(normalize_suburl(spelling), "")


class PrefixRelativeUrlTests(unittest.TestCase):
    def test_given_no_suburl_it_should_return_the_url_unchanged(self):
        self.assertEqual(prefix_relative_url("/api/", ""), "/api/")

    def test_given_a_root_relative_url_it_should_prefix_it_and_stay_root_relative(self):
        # these urls are compared against request.path and handed to browsers
        # as redirect targets, so losing the leading slash silently breaks both
        self.assertEqual(prefix_relative_url("/api/", "argus/"), "/argus/api/")

    def test_given_the_root_url_it_should_become_the_suburl_root(self):
        self.assertEqual(prefix_relative_url("/", "argus/"), "/argus/")

    def test_given_an_already_prefixed_url_it_should_not_prefix_it_twice(self):
        self.assertEqual(prefix_relative_url("/argus/api/", "argus/"), "/argus/api/")

    def test_given_a_url_that_merely_starts_with_the_same_letters_it_should_still_prefix(self):
        self.assertEqual(prefix_relative_url("/argusly/", "argus/"), "/argus/argusly/")

    def test_given_the_bare_prefix_it_should_gain_the_trailing_slash(self):
        # anything else would leak the one output that cannot be compared
        # against request.path safely: "/argus" also prefix-matches "/argusly/"
        self.assertEqual(prefix_relative_url("/argus", "argus/"), "/argus/")

    def test_given_an_absolute_url_it_should_be_left_alone(self):
        # STATIC_URL may well point at a CDN, which is nobody's sub-site
        self.assertEqual(prefix_relative_url("https://cdn.example.org/", "argus/"), "https://cdn.example.org/")

    def test_given_a_protocol_relative_url_it_should_be_left_alone(self):
        # "//host/path" starts with a slash but addresses another host, and is
        # the canonical way to write a scheme-agnostic CDN url
        self.assertEqual(prefix_relative_url("//cdn.example.org/static/", "argus/"), "//cdn.example.org/static/")

    def test_given_a_genuinely_relative_url_it_should_be_left_alone(self):
        self.assertEqual(prefix_relative_url("api/", "argus/"), "api/")

    def test_given_an_unnormalized_suburl_it_should_prefix_as_if_it_were_normalized(self):
        for spelling in ("argus", "/argus", "argus/", "/argus/"):
            with self.subTest(spelling=spelling):
                self.assertEqual(prefix_relative_url("/api/", spelling), "/argus/api/")


class AppendSuburlTests(unittest.TestCase):
    def test_given_no_suburl_it_should_return_the_url_unchanged(self):
        self.assertEqual(append_suburl("https://example.org", ""), "https://example.org")

    def test_given_an_empty_url_it_should_stay_empty(self):
        # permalinks are simply not configured; do not invent a host for them
        self.assertEqual(append_suburl("", "argus/"), "")

    def test_given_a_url_it_should_gain_the_suburl_and_a_trailing_slash(self):
        for url in ("https://example.org", "https://example.org/"):
            with self.subTest(url=url):
                self.assertEqual(append_suburl(url, "argus/"), "https://example.org/argus/")

    def test_given_a_url_that_already_ends_in_the_suburl_it_should_not_repeat_it(self):
        for url in ("https://example.org/argus", "https://example.org/argus/", "https://example.org/argus//"):
            with self.subTest(url=url):
                self.assertEqual(append_suburl(url, "argus/"), "https://example.org/argus/")

    def test_given_a_url_whose_last_segment_merely_ends_in_the_suburl_it_should_append(self):
        # "myfoo" is not "/foo", however much it looks like it from the right
        self.assertEqual(append_suburl("https://example.org/myfoo", "foo/"), "https://example.org/myfoo/foo/")

    def test_given_a_host_named_after_the_suburl_it_should_still_append(self):
        self.assertEqual(append_suburl("https://argus.example.org", "argus/"), "https://argus.example.org/argus/")

    def test_given_a_suffixed_url_then_joining_a_relative_path_should_keep_the_suburl(self):
        # the trailing slash exists for this: urljoin drops the last segment
        # of a base without one, and permalinks are built this way
        frontend_url = append_suburl("https://example.org", "argus/")
        self.assertEqual(urljoin(frontend_url, "incidents/5"), "https://example.org/argus/incidents/5")


class GetUrlPatternsFromSettingsTest(unittest.TestCase):
    def test_when_setting_is_falsey_return_empty_list(self):
        self.assertEqual(get_urlpatterns(None), [])

    def test_when_setting_urls_is_falsey_it_should_return_empty_list(self):
        class Obj:
            pass

        obj = Obj()
        obj.urls = None

        self.assertEqual(get_urlpatterns([obj]), [])

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
        result = get_urlpatterns([setting])
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
        result = get_urlpatterns([setting])
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
        app_setting = AppSetting(**raw_setting)
        result = update_context_processors_list(TEMPLATES, [app_setting])
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
