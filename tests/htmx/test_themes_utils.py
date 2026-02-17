from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import tag

from argus.htmx.themes.utils import get_theme_names_from_setting, get_theme_names


@tag("unit")
class TestGetThemeNamesFromSetting(TestCase):
    def test_get_theme_names_from_setting_with_str_theme_returns_name(self):
        raw_themes = ["a"]
        with patch("argus.htmx.themes.utils.get_raw_themes_setting", return_value=raw_themes):
            result = get_theme_names_from_setting()
            self.assertEqual(result, raw_themes)

    def test_get_theme_names_from_Setting_with_dict_theme_returns_name(self):
        raw_themes = [{"b": None}]
        with patch("argus.htmx.themes.utils.get_raw_themes_setting", return_value=raw_themes):
            result = get_theme_names_from_setting()
            self.assertEqual(result, ["b"])


@tag("unit")
class TestGetThemeNames(TestCase):
    def test_get_theme_names_golden_path(self):
        theme_names_from_setting = ["a", "b"]
        theme_names_from_css = ["", "a", "b", "c"]
        with patch("argus.htmx.themes.utils.get_theme_names_from_setting", return_value=theme_names_from_setting):
            with patch("argus.htmx.themes.utils.get_theme_names_from_css", return_value=theme_names_from_css):
                result = get_theme_names()
                self.assertEqual(result, set(theme_names_from_setting))

    def test_get_theme_names_if_theme_missing_will_raise_exception(self):
        theme_names_from_setting = ["a", "b"]
        theme_names_from_css = ["", "b", "c"]
        with patch("argus.htmx.themes.utils.get_theme_names_from_setting", return_value=theme_names_from_setting):
            with patch("argus.htmx.themes.utils.get_theme_names_from_css", return_value=theme_names_from_css):
                with self.assertRaises(ImproperlyConfigured):
                    get_theme_names(quiet=False)
