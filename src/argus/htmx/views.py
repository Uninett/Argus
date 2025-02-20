from django.views.generic.base import RedirectView


class IncidentListRedirectView(RedirectView):
    "Redirect to incident list, which may trigger a login"

    permanent = False
    query_string = False
    pattern_name = "htmx:incident-list"
