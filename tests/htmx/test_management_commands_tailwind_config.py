from unittest import TestCase

from django.test import tag

from argus.htmx.tailwindtheme.cssconfig import generate_theme_css


@tag("unit")
class TestGenerateThemeCss(TestCase):
    def test_empty_config_dict_still_generates_css(self):
        expected = '@plugin "daisyui/theme" {\n  name: "foo";\n}\n'
        result = generate_theme_css("foo", {})
        self.assertEqual(result, expected)

    def test_css_variable_is_not_quoted(self):
        result = generate_theme_css("foo", {"--foo": "XX"})
        self.assertIn("--foo: XX;", result)

    def test_non_css_variable_is_quoted(self):
        result = generate_theme_css("foo", {"foo": "XX"})
        self.assertIn('foo: "XX";', result)
