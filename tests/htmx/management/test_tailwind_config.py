import io
import tempfile
import pathlib

from django import test
from django.test import override_settings

from argus.htmx.management.commands.tailwind_config import Command
from argus.htmx.tailwindtheme.cssconfig import generate_theme_css, render_styles_css


class TestGenerateThemeCss(test.SimpleTestCase):
    def test_given_theme_config_then_generates_valid_css_block(self):
        css = generate_theme_css("mytheme", {"color-scheme": "light", "--color-primary": "#006d91"})
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
            theme_file = css_path.parent / "custom-themes" / "mytheme.css"
            self.assertTrue(theme_file.exists())
            self.assertIn("mytheme", theme_file.read_text())


class TestRenderStylesCss(test.SimpleTestCase):
    def test_given_css_files_then_renders_imports(self):
        template = "@import './tailwind.css';\n{% for cssfile in cssfiles %}@import './{{ cssfile }}';\n{% endfor %}"
        output = render_styles_css(template, ["base.css", "extra.css"])
        self.assertIn("@import './base.css'", output)
        self.assertIn("@import './extra.css'", output)
