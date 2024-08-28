from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django_htmx.middleware import HtmxDetails

from argus.incident.models import Incident
from argus.util.datetime_utils import make_aware

from .customization import get_incident_table_columns
from .utils import get_filter_function
from .forms import AckForm


User = get_user_model()
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


# fetch with htmx
def incident_row(request, pk: int):
    incident = get_object_or_404(Incident, d=pk)
    context = {
        "incident": incident,
    }
    return render(request, "htmx/incidents/_incident_row.html", context=context)


def incident_detail(request, pk: int):
    incident = get_object_or_404(Incident, id=pk)
    action_endpoints = {
        "ack": reverse("htmx:incident-detail-add-ack", kwargs={"pk": pk}),
    }
    context = {
        "incident": incident,
        "endpoints": action_endpoints,
        "page_title": str(incident),
    }
    return render(request, "htmx/incidents/incident_detail.html", context=context)


def _incident_add_ack(pk: int, formdata, user: User, group: Optional[str] = None):
    incident = get_object_or_404(Incident, id=pk)
    is_group_member = None
    if group:
        group = get_object_or_404(Group, name=group)
        is_group_member = user.groups.filter(pk=group.pk).exists()
    form = AckForm()
    if formdata:
        if group and not is_group_member:
            raise PermissionDenied("User {request.user} is not a member of the correct group")
        form = AckForm(formdata)
        if form.is_valid():
            incident.create_ack(
                user,
                description=form.cleaned_data["description"],
                expiration=form.cleaned_data["expiration"],
            )
    context = {
        "form": form,
        "incident": incident,
        "page_title": str(incident),
        'group': group,
        'is_group_member': is_group_member,
    }
    return incident, context


def incident_add_ack(request, pk: int, group: Optional[str] = None):
    formdata = request.POST or None
    _, context = _incident_add_ack(pk, formdata, request.user, group)
    return render(request, "htmx/incidents/incident_add_ack.html", context=context)


@require_POST
def incident_detail_add_ack(request, pk: int, group: Optional[str] = None):
    formdata = request.POST or None
    _incident_add_ack(pk, formdata, request.user, group)
    return redirect("htmx:incident-detail", pk=pk)


@require_GET
def incident_list(request: HtmxHttpRequest) -> HttpResponse:
    columns = get_incident_table_columns()

    # Load incidents
    qs = prefetch_incident_daughters().order_by("-start_time")
    total_count = qs.count()
    last_refreshed = make_aware(datetime.now())

    params = dict(request.GET.items())

    incident_list_filter = get_filter_function()
    filter_form, qs = incident_list_filter(request, qs)
    filtered_count = qs.count()

    # Standard Django pagination
    page_num = params.pop("page", "1")
    PAGE_SIZE = 10
    paginator = Paginator(object_list=qs, per_page=PAGE_SIZE)
    page = paginator.get_page(page_num)

    # The htmx magic - use a different, minimal base template for htmx
    # requests, allowing us to skip rendering the unchanging parts of the
    # template.
    if request.htmx:
        base_template = "htmx/incidents/responses/_incidents_table_refresh.html"
    else:
        base_template = "htmx/incidents/_base.html"
    context = {
        "columns": columns,
        "filtered_count": filtered_count,
        "count": total_count,
        "filter_form": filter_form,
        "page_title": "Incidents",
        "base": base_template,
        "page": page,
        "last_refreshed": last_refreshed,
        "update_interval": 30,
        "per_page": PAGE_SIZE,
    }

    return render(request, "htmx/incidents/incident_list.html", context=context)
