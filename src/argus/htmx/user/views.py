from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import get_preference_obj, save_preferences
from argus.htmx.incident.columns import get_incident_table_columns
from argus.htmx.incident.views import HtmxHttpRequest
from argus.htmx.user.preferences.utils import setup_preference_forms
from argus.incident.models import Incident

THEME_PREFERENCES = ["theme", "datetime_format_name"]


@require_GET
def user_preferences(request) -> HttpResponse:
    """Renders the main preferences page for a user"""
    forms = setup_preference_forms(request)
    theme_forms = [form for name, form in forms.items() if name in THEME_PREFERENCES]
    incident_forms = [form for name, form in forms.items() if name not in THEME_PREFERENCES]

    preferences = request.user.get_preferences_context()
    preferences_data = preferences.get("argus_htmx", {})

    context = {
        "page_title": "User preferences",
        "forms": forms,
        "theme_forms": theme_forms,
        "incident_forms": incident_forms,
        **_get_incident_table_context(preferences_data),
    }

    return render(request, "htmx/user/preferences_list.html", context=context)


@require_GET
def incident_table_preview(request) -> HttpResponse:
    """Render a preview of the incident table based on selected preferences."""
    preferences = request.user.get_preferences_context()
    preferences_data = preferences.get("argus_htmx", {})
    preferences_data.update(request.GET.dict())

    context = {
        **_get_incident_table_context(preferences_data),
        "preferences": preferences,
    }

    return render(request, "htmx/incident/_unpaged_incident_table.html", context=context)


def _get_incident_table_context(preferences_data: dict) -> dict:
    """Extract common logic for incident table rendering."""
    selected_layout = preferences_data.get("incidents_table_layout", "standard")
    preferences_data["incidents_table_layout_compact"] = selected_layout == "compact"
    column_layout_name = preferences_data.get("incidents_table_column_name", "built-in")
    columns = get_incident_table_columns(column_layout_name)

    return {
        "dummy_column": True,
        "columns": columns,
        "incident_list": Incident.objects.all()[:1],
    }


@require_POST
def update_preferences(request: HtmxHttpRequest, namespace: str) -> HttpResponse:
    try:
        prefs = get_preference_obj(request, namespace)
    except ValueError:
        raise Http404(f"Invalid namespace '{namespace}'")

    saved, failed = save_preferences(request, request.POST, prefs)

    if not request.htmx:
        # We're only expecting htmx requests, but let's make sure to behave decently in case of a regular request
        return HttpResponseRedirect(request.META.HTTP_REFERER or settings.LOGIN_REDIRECT_URL)

    # special case if we're only updating a single preference that has a partial template
    # defined
    if len(saved) == 1 and not failed and (template := prefs.FIELDS[saved[0]].partial_response_template) is not None:
        return render(request, template)

    return HttpResponseClientRefresh()
