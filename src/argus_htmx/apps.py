import pathlib
from django.apps import AppConfig


class HtmxFrontendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "argus_htmx"
    name = "argus_htmx"

    def tailwind_css_files(self):
        yield from pathlib.Path(__file__).parent.glob("tailwindtheme/snippets/*.css")
