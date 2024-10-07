import pathlib
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template import engines
from django.template.context import make_context
from django.template import Template

from argus_htmx.themes.utils import get_themes
from argus_htmx import settings as argus_htmx_settings


# Copied from https://github.com/GEANT/geant-argus/pull/15 with minor modifications
class Command(BaseCommand):
    help = """
    Uses the template specified in the TAILWIND_CONFIG_TEMPLATE setting
    (default: tailwind.config.js) to dynamically build a tailwind.config.js.
    The template should contain:

    - a "{{ daisyuithemes }}" section without square brackets that will be
      popuplated by the daisyUI theme list specified in the DAISYUI_THEMES
      setting (default: ["dark", "light", {"argus"": {...}} ])

    - a "{{ themeoverride }}" section that will be popuplated by a dict
      containing tailwind theme options specified in TAILWIND_THEME_OVERRIDE
      setting (default: {})
    """
    DEFAULT_TEMPLATE_PATH = "src/argus_htmx/tailwindtheme/tailwind.config.template.js"
    DEFAULT_TARGET = "src/argus_htmx/tailwindtheme/tailwind.config.js"

    def handle(self, *args, **options):
        template_loc = getattr(settings, "TAILWIND_CONFIG_TEMPLATE", self.DEFAULT_TEMPLATE_PATH)
        target_path = getattr(settings, "TAILWIND_CONFIG_TARGET", self.DEFAULT_TARGET)

        context = {
            "themeoverride": getattr(settings, "TAILWIND_THEME_OVERRIDE", argus_htmx_settings.TAILWIND_THEME_OVERRIDE),
            "daisyuithemes": get_themes(),
        }
        template_path = pathlib.Path(template_loc)
        if not template_path.is_file():
            self.stdout.write(f"{template_loc} is not a file")
            return

        pathlib.Path(target_path).write_text(self.render_config(template_path=template_path, context=context))

        self.stdout.write(f"Wrote tailwind config to '{target_path}'")

    @staticmethod
    def render_config(template_path: pathlib.Path, context):
        template = Template(template_path.read_text())
        return template.render(make_context(context, autoescape=False))
