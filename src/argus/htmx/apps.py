import pathlib

from django.apps import AppConfig


class HtmxFrontendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "argus_htmx"
    name = "argus.htmx"

    def tailwind_css_files(self):
        tailwindtheme_dir = pathlib.Path(__file__).parent / "tailwindtheme"
        yield from tailwindtheme_dir.glob("snippets/*.css")
        yield from tailwindtheme_dir.glob("themes/*.css")

    def ready(self):
        # Register checks
        from .checks import check_for_valid_themes_list  # noqa: F401
