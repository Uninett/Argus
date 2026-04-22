from django import test
from django.test import override_settings

from argus.htmx.themes.utils import (
    DEPRECATED_THEME_NAMES,
    clean_themes,
    get_theme_default,
    get_theme_names_from_setting,
    resolve_theme_name,
)
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


class TestResolveThemeName(test.SimpleTestCase):
    def test_given_current_name_then_passes_through(self):
        self.assertEqual(resolve_theme_name("light"), "light")
        self.assertEqual(resolve_theme_name("dark"), "dark")
        self.assertEqual(resolve_theme_name("argus"), "argus")

    def test_given_deprecated_name_then_returns_new_name(self):
        for old_name, new_name in DEPRECATED_THEME_NAMES.items():
            with self.assertLogs("argus.htmx.themes.utils", level="WARNING"):
                self.assertEqual(resolve_theme_name(old_name), new_name)

    def test_given_unknown_name_then_passes_through(self):
        self.assertEqual(resolve_theme_name("custom"), "custom")


class TestCleanThemesDeprecatedNames(test.SimpleTestCase):
    def test_given_deprecated_string_entries_then_resolves_them(self):
        with self.assertLogs("argus.htmx.themes.utils", level="WARNING"):
            result = clean_themes(["sikt", "argus", "sikt-dark"])
        self.assertEqual(result, ["light", "argus", "dark"])

    def test_given_both_old_and_new_name_then_keeps_both(self):
        with self.assertLogs("argus.htmx.themes.utils", level="WARNING"):
            result = clean_themes(["light", "sikt"])
        self.assertEqual(result, ["light", "light"])


class TestGetThemeDefaultDeprecated(test.SimpleTestCase):
    @override_settings(THEME_DEFAULT="sikt")
    def test_given_deprecated_default_then_resolves_to_light(self):
        with self.assertLogs("argus.htmx.themes.utils", level="WARNING"):
            self.assertEqual(get_theme_default(), "light")

    @override_settings(THEME_DEFAULT="sikt-dark")
    def test_given_deprecated_dark_default_then_resolves_to_dark(self):
        with self.assertLogs("argus.htmx.themes.utils", level="WARNING"):
            self.assertEqual(get_theme_default(), "dark")

    @override_settings(THEME_DEFAULT="argus")
    def test_given_current_default_then_passes_through(self):
        self.assertEqual(get_theme_default(), "argus")
