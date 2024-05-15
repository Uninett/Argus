import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, reverse, get_object_or_404

from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django_htmx.middleware import HtmxDetails

from argus.incident.models import Incident

from .forms import AckForm

LOG = logging.getLogger(__name__)


def prefetch_incident_daughters():
    return (
        Incident.objects
        .select_related("source")
        .prefetch_related(
            "incident_tag_relations",
            "incident_tag_relations__tag",
            "events",
            "events__ack",
        )
    )


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


def incidents(request):
    qs = prefetch_incident_daughters().order_by("-start_time")
    latest = qs.latest("start_time").start_time
    context = {
        "qs": qs[:5],
        "latest": latest,
        "count": qs.count(),
        "page_title": "Incidents",
    }
    return render(request, "htmx/incidents/list.html", context=context)


# fetch with htmx
def incident_row(request, pk: int):
    incident = get_object_or_404(Incident, d=pk)
    context = {
        "incident": incident,
    }
    return render(request, "htmx/incidents/_incident_row.html", context=context)


def incident_detail(request, pk: int):
    incident = get_object_or_404(Incident, id=pk)
    context = {
        "incident": incident,
        "page_title": str(incident),
    }
    return render(request, "htmx/incidents/incident_detail.html", context=context)


def incident_add_ack(request, pk: int, group: Optional[str] = None):
    incident = get_object_or_404(Incident, id=pk)
    is_group_member = None
    if group:
        group = get_object_or_404(Group, name=group)
        is_group_member = request.user.groups.filter(pk=group.pk).exists()
    context = {
        "form": AckForm,
        "incident": incident,
        "page_title": str(incident),
        'group': group,
        'is_group_member': is_group_member,
    }
    if request.POST:
        if group and not is_group_member:
            raise PermissionDenied("User {request.user} is not a member of the correct group")
        form = AckForm(request.POST)
        if form.is_valid():
            incident.create_ack(
                request.user,
                description=form.cleaned_data["description"],
                expiration=form.cleaned_data["expiration"],
            )
    return render(request, "htmx/incidents/incident_add_ack.html", context=context)


@require_GET
def incidents_table(request: HtmxHttpRequest) -> HttpResponse:
    # Load incidents
    qs = Incident.objects.all().order_by("-start_time")
    latest = qs.latest("start_time").start_time

    # Standard Django pagination
    page_num = request.GET.get("page", "1")
    page = Paginator(object_list=qs, per_page=10).get_page(page_num)

    # The htmx magic - use a different, minimal base template for htmx
    # requests, allowing us to skip rendering the unchanging parts of the
    # template.
    if request.htmx:
        base_template = "htmx/incidents/_incidents_table.html"
    else:
        base_template = "htmx/incidents/_base.html"

    context = {
        "qs": qs,
        "latest": latest,
        "page_title": "Incidents",
        "base": base_template,
        "page": page,
    }

    return render(
        request,
        "htmx/incidents/incidents_list.html",
        context=context
    )
