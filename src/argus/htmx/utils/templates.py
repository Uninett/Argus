# Do not import any models

from django.template import engines
from django.template.context import make_context
from django.template.loader import get_template


def render_to_string(template_name: str, context, autoescape: bool = False) -> str:
    template = get_template(template_name)
    fixed_context = make_context(context, autoescape=autoescape)
    rendered_template = template.template.render(fixed_context)
    return rendered_template


def get_template_dirs():
    for engine in engines.all():
        yield from getattr(engine, "template_dirs", [])
