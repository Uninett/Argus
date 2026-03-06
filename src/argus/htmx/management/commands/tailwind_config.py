import pathlib
from django.apps import apps
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import get_template

from argus.htmx.tailwindtheme.cssconfig import generate_config
from argus.htmx.themes.utils import clean_themes, get_raw_themes_setting


# Copied from https://github.com/GEANT/geant-argus/pull/15 with minor modifications
class Command(BaseCommand):
    help = """
    Generates CSS configuration files for Tailwind CSS v4 and DaisyUI v5.

    This command generates:

    1. A `styles.css` file that imports all CSS snippets from installed apps.
       Apps may define a `tailwind_css_files` method that returns paths to CSS
       files to include. (see argus.htmx.apps.HtmxFrontendConfig for an example)

    2. A `tailwind.css` file with the base Tailwind/DaisyUI configuration
       (imported first by styles.css).

    3. CSS theme files in `custom-themes/` for custom themes defined in the
       DAISYUI_THEMES setting. Custom themes are defined as dicts with CSS
       variables, e.g.:
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
    DEFAULT_TAILWIND_TEMPLATE_NAME = "tailwind/tailwind.css"

    def handle(self, *args, **options):
        css_template_name = getattr(settings, "TAILWIND_CSS_TEMPLATE", self.DEFAULT_CSS_TEMPLATE_NAME)
        css_target_path = pathlib.Path(getattr(settings, "TAILWIND_CSS_TARGET", self.DEFAULT_CSS_TARGET))
        output_dir = css_target_path.parent

        themes = clean_themes(get_raw_themes_setting())
        tailwind_template = self.read_template_source(self.DEFAULT_TAILWIND_TEMPLATE_NAME)
        styles_template = self.read_template_source(css_template_name)
        css_files = self.get_css_files(output_dir)

        generate_config(themes, tailwind_template, styles_template, css_files, output_dir, log=self.stdout.write)

    @staticmethod
    def read_template_source(template_name: str) -> str:
        """Read raw template source text via Django's template discovery."""
        template = get_template(template_name)
        return template.template.source

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
