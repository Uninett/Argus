import pathlib
from django.apps import apps
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template import engines
from django.template.context import make_context
from django.template.loader import get_template

from argus.htmx.themes.utils import get_raw_themes_setting


# Copied from https://github.com/GEANT/geant-argus/pull/15 with minor modifications
class Command(BaseCommand):
    help = """
    Generates CSS configuration files for Tailwind CSS v4 and DaisyUI v5.

    This command generates:

    1. A `styles.css` file that imports all CSS snippets from installed apps.
       Apps may define a `tailwind_css_files` method that returns paths to CSS
       files to include. (see argus.htmx.apps.HtmxFrontendConfig for an example)

    2. CSS theme files for custom themes defined in the DAISYUI_THEMES setting.
       Custom themes are defined as dicts with CSS variables, e.g.:
       DAISYUI_THEMES = ["dark", "light", {"mytheme": {"--color-primary": "#006d91", ...}}]
       Built-in themes (strings like "dark", "light") are handled by DaisyUI directly.

    Settings:
     - TAILWIND_CSS_TARGET: target location for the base styles.css file
       (default: src/argus/htmx/tailwindtheme/styles.css)
     - TAILWIND_CSS_TEMPLATE: template for generating styles.css
       (default: tailwind/styles.css)
     - DAISYUI_THEMES: list of themes to enable (strings for built-in, dicts for custom)
    """
    DEFAULT_CSS_TEMPLATE_NAME = "tailwind/styles.css"
    DEFAULT_CSS_TARGET = "src/argus/htmx/tailwindtheme/styles.css"

    def handle(self, *args, **options):
        css_template_name = getattr(settings, "TAILWIND_CSS_TEMPLATE", self.DEFAULT_CSS_TEMPLATE_NAME)
        css_target_path = pathlib.Path(getattr(settings, "TAILWIND_CSS_TARGET", self.DEFAULT_CSS_TARGET))

        # Generate theme CSS files from DAISYUI_THEMES setting
        themes_dir = css_target_path.parent / "themes"
        themes_dir.mkdir(exist_ok=True)
        self.generate_theme_files(themes_dir)

        # Generate main styles.css
        self.write_file(
            css_template_name,
            css_target_path,
            context=self.get_context(target_dir=css_target_path.parent),
            name="tailwind base css",
        )

    def generate_theme_files(self, snippets_dir: pathlib.Path):
        """Generate CSS theme files from DAISYUI_THEMES setting."""
        themes_setting = get_raw_themes_setting()

        for theme in themes_setting:
            if isinstance(theme, dict):
                for theme_name, theme_config in theme.items():
                    self.write_theme_file(snippets_dir, theme_name, theme_config)

    def write_theme_file(self, themes_dir: pathlib.Path, theme_name: str, theme_config: dict):
        """Write a single theme CSS file."""
        css_content = self.generate_theme_css(theme_name, theme_config)
        target_path = themes_dir / f"{theme_name}.css"
        target_path.write_text(css_content)
        self.stdout.write(f"Wrote theme '{theme_name}' to '{target_path}'")

    def generate_theme_css(self, theme_name: str, theme_config: dict) -> str:
        """Generate CSS content for a DaisyUI v5 theme.

        Theme config keys are passed through directly as CSS properties.
        Keys starting with '--' are written as-is, other keys are written
        without the '--' prefix (for DaisyUI plugin options like color-scheme).
        """
        lines = [
            '@plugin "daisyui/theme" {',
            f'  name: "{theme_name}";',
        ]

        for key, value in theme_config.items():
            if key.startswith("--"):
                lines.append(f"  {key}: {value};")
            else:
                # Non-variable keys like color-scheme, default, prefersdark
                lines.append(f'  {key}: "{value}";')

        lines.append("}")
        lines.append("")  # trailing newline

        return "\n".join(lines)

    def get_context(self, target_dir: pathlib.Path):
        return {
            "cssfiles": self.get_css_files(target_dir),
        }

    def write_file(self, template_name, target_path, context, name):
        pathlib.Path(target_path).write_text(self.render(template_name=template_name, context=context))

        self.stdout.write(f"Wrote {name} to '{target_path}'")

    @staticmethod
    def render(template_name: str, context):
        template = get_template(template_name)
        return template.template.render(make_context(context, autoescape=False))

    @staticmethod
    def get_template_dirs():
        for engine in engines.all():
            yield from getattr(engine, "template_dirs", [])

    @classmethod
    def get_css_files(cls, target_dir: pathlib.Path):
        css_files = sorted(cls._iter_css_files(), key=lambda p: p.stem)
        return (cls.make_relative(p, target_dir) for p in css_files)

    @staticmethod
    def _iter_css_files():
        for app in apps.get_app_configs():
            if callable(css_files := getattr(app, "tailwind_css_files", None)):
                yield from (pathlib.Path(p) for p in css_files())

    @staticmethod
    def make_relative(path: pathlib.Path, base_path: pathlib.Path):
        try:
            return path.relative_to(base_path.absolute())
        except ValueError:
            return path
