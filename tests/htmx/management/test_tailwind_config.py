import io
import tempfile
import pathlib

from django import test
from django.test import override_settings

from argus.htmx.management.commands.tailwind_config import Command


class TestGetThemesContext(test.SimpleTestCase):
    def test_given_string_themes_then_lists_as_builtin(self):
        command = Command()
        context = command.get_themes_context(["dark", "light"])
        self.assertEqual(context["builtin_themes"], "dark, light")

    def test_given_non_string_entries_then_ignores_them(self):
        command = Command()
        context = command.get_themes_context(["dark", {"mytheme": {"primary": "#fff"}}, 42, "light"])
        self.assertEqual(context["builtin_themes"], "dark, light")

    def test_given_dict_themes_then_excludes_from_builtin(self):
        command = Command()
        context = command.get_themes_context(["dark", {"mytheme": {"primary": "#fff"}}, "light"])
        self.assertEqual(context["builtin_themes"], "dark, light")


class TestGenerateThemeCss(test.SimpleTestCase):
    def test_given_theme_config_then_generates_valid_css_block(self):
        command = Command()
        css = command.generate_theme_css("mytheme", {"color-scheme": "light", "--color-primary": "#006d91"})
        self.assertIn('@plugin "daisyui/theme"', css)
        self.assertIn('name: "mytheme"', css)
        self.assertIn("--color-primary: #006d91;", css)
        self.assertIn('color-scheme: "light"', css)


class TestHandle(test.SimpleTestCase):
    def test_given_custom_theme_then_creates_expected_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            css_path = pathlib.Path(tmpdir) / "styles.css"
            (pathlib.Path(tmpdir) / "snippets").mkdir()
            with override_settings(
                TAILWIND_CSS_TARGET=str(css_path),
                DAISYUI_THEMES=["dark", {"mytheme": {"color-scheme": "light"}}],
            ):
                command = Command()
                command.stdout = io.StringIO()
                command.handle()
            self.assertTrue(css_path.exists())
            theme_file = css_path.parent / "themes" / "mytheme.css"
            self.assertTrue(theme_file.exists())
            self.assertIn("mytheme", theme_file.read_text())


class TestRender(test.SimpleTestCase):
    def test_given_css_files_then_renders_imports(self):
        context = {"cssfiles": ["base.css", "extra.css"]}
        output = Command.render(template_name="tailwind/styles.css", context=context)
        self.assertIn("@import './base.css'", output)
        self.assertIn("@import './extra.css'", output)
