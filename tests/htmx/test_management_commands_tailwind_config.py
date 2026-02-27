from unittest import TestCase
from unittest.mock import patch

from django.test import override_settings, tag

from argus.htmx.management.commands.tailwind_config import Command


class TestHandle(TestCase):
    @override_settings(DAISYUI_THEMES=("light",))
    def test_handle_does_not_raise_exceptions(self):
        cmd = Command()
        try:
            cmd.handle()
        except Exception as e:
            self.fail(f"Handle raised an exception: {e}")


class TestGenerateThemeFile(TestCase):

    @override_settings(DAISYUI_THEMES=("light", "dark"))
    def test_generate_nothing_if_no_dicts_in_DAISYUI_THEMES_setting(self):
        cmd = Command()
        with patch("argus.htmx.management.commands.tailwind_config.Command.write_theme_file") as writer:
            cmd.generate_theme_files("/tmp")
            writer.assert_not_called()

    @override_settings(DAISYUI_THEMES=({},))
    def test_generate_nothing_if_empty_dicts_in_DAISYUI_THEMES_setting(self):
        cmd = Command()
        with patch("argus.htmx.management.commands.tailwind_config.Command.write_theme_file") as writer:
            cmd.generate_theme_files("/tmp")
            writer.assert_not_called()

    @override_settings(DAISYUI_THEMES=({"mytheme": {}},))
    def test_generate_n_files_if_n_valid_dicts_in_DAISYUI_THEMES_setting(self):
        cmd = Command()
        with patch("argus.htmx.management.commands.tailwind_config.Command.write_theme_file") as writer:
            cmd.generate_theme_files("/tmp")
            writer.assert_called_once()


@tag("unit")
class TestGenerateThemeCss(TestCase):

    def test_empty_config_dict_still_generates_css(self):
        cmd = Command()
        expected = '@plugin "daisyui/theme" {\n  name: "foo";\n}\n'
        result = cmd.generate_theme_css("foo", {})
        self.assertEqual(result, expected)

    def test_css_variable_is_not_quoted(self):
        cmd = Command()
        result = cmd.generate_theme_css("foo", {"--foo": "XX"})
        self.assertIn("--foo: XX;", result)

    def test_non_css_variable_is_quoted(self):
        cmd = Command()
        result = cmd.generate_theme_css("foo", {"foo": "XX"})
        self.assertIn('foo: "XX";', result)
