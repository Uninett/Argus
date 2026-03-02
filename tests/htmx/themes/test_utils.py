from django import test
from django.test import override_settings

from argus.htmx.themes.utils import clean_themes, get_theme_names_from_setting
from argus.htmx import defaults as fallbacks


class TestCleanThemes(test.SimpleTestCase):
    def test_given_valid_entries_then_passes_through(self):
        themes = ["dark", {"mytheme": {"primary": "#fff"}}, "light"]
        self.assertEqual(clean_themes(themes), themes)
        self.assertEqual(clean_themes(fallbacks.DEFAULT_THEMES), fallbacks.DEFAULT_THEMES)

    def test_given_invalid_entries_then_skips_them(self):
        themes = ["dark", "", {}, None, {"": {"primary": "#fff"}}, {"bad": None}, {42: {"primary": "#fff"}}, "light"]
        self.assertEqual(clean_themes(themes), ["dark", "light"])

    def test_given_empty_colors_dict_then_keeps_entry(self):
        self.assertEqual(clean_themes([{"mytheme": {}}]), [{"mytheme": {}}])

    def test_given_multi_key_dict_then_splits_into_single_keys(self):
        entry = {"theme_a": {"primary": "#000"}, "theme_b": {"primary": "#fff"}}
        self.assertEqual(
            clean_themes([entry]),
            [{"theme_a": {"primary": "#000"}}, {"theme_b": {"primary": "#fff"}}],
        )

    def test_given_empty_dict_entry_then_warns(self):
        with self.assertLogs("argus.htmx.themes.utils", level="WARNING") as cm:
            clean_themes([{}])
        self.assertIn("empty dict", cm.output[0])

    def test_given_none_entry_then_warns(self):
        with self.assertLogs("argus.htmx.themes.utils", level="WARNING") as cm:
            clean_themes([None])
        self.assertIn("NoneType", cm.output[0])

    def test_given_non_string_dict_key_then_warns(self):
        with self.assertLogs("argus.htmx.themes.utils", level="WARNING") as cm:
            clean_themes([{42: {"primary": "#fff"}}])
        self.assertIn("invalid key", cm.output[0])


class TestGetThemesFromSetting(test.SimpleTestCase):
    @override_settings(DAISYUI_THEMES=["dark", "light", "cupcake"])
    def test_given_string_themes_then_returns_names(self):
        self.assertEqual(get_theme_names_from_setting(), ["dark", "light", "cupcake"])

    @override_settings(DAISYUI_THEMES=[{"mytheme": {"primary": "#fff"}}])
    def test_given_dict_themes_then_returns_key_as_name(self):
        self.assertEqual(get_theme_names_from_setting(), ["mytheme"])

    @override_settings(DAISYUI_THEMES=["dark", {"mytheme": {"primary": "#fff"}}, "light"])
    def test_given_mixed_themes_then_returns_all_names(self):
        self.assertEqual(get_theme_names_from_setting(), ["dark", "mytheme", "light"])

    @override_settings(DAISYUI_THEMES=["dark", None, "", 42, "light"])
    def test_given_invalid_entries_then_filters_them_out(self):
        self.assertEqual(get_theme_names_from_setting(), ["dark", "light"])
