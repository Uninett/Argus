"""
This should probably be in a separate 3rd party theming-app!

How to use:

Update the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with *one* of these.

See django settings for ``TEMPLATES``.
"""

def theme_via_GET(request):
    theme = request.GET.get("theme", None)
    return {"theme": theme}


def theme_via_session(request):
    theme = request.session.get("theme", None)
    return {"theme": theme}
