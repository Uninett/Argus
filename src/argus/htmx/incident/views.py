from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from django import forms
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.timezone import now as tznow
from django.shortcuts import render, get_object_or_404

from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseBadRequest
from django_htmx.http import HttpResponseClientRefresh, reswap, retarget

from argus.auth.utils import get_or_update_preference
from argus.incident.models import Incident
from argus.incident.ticket.utils import get_ticket_plugin_path
from argus.notificationprofile.models import Filter
from argus.util.datetime_utils import make_aware

from ..request import HtmxHttpRequest

from .customization import get_incident_table_columns
from .utils import get_filter_function
from .forms import AckForm, DescriptionOptionalForm, EditTicketUrlForm, AddTicketUrlForm
from ..utils import (
    single_autocreate_ticket_url_queryset,
    bulk_change_incidents,
    bulk_ack_queryset,
    bulk_close_queryset,
    bulk_reopen_queryset,
    bulk_change_ticket_url_queryset,
)

User = get_user_model()
LOG = logging.getLogger(__name__)


# Map request trigger to parameters for incidents update
INCIDENT_UPDATE_ACTIONS = {
    "ack": (AckForm, bulk_ack_queryset),
    "close": (DescriptionOptionalForm, bulk_close_queryset),
    "reopen": (DescriptionOptionalForm, bulk_reopen_queryset),
    "update-ticket": (EditTicketUrlForm, bulk_change_ticket_url_queryset),
    "add-ticket": (AddTicketUrlForm, bulk_change_ticket_url_queryset),
    "autocreate-ticket": (None, single_autocreate_ticket_url_queryset),
}


def prefetch_incident_daughters():
    return Incident.objects.select_related("source").prefetch_related(
        "incident_tag_relations",
        "incident_tag_relations__tag",
        "events",
        "events__ack",
    )


# fetch with htmx
@require_GET
def incident_detail(request, pk: int):
    incident = get_object_or_404(Incident, id=pk)
    duration = None
    now = tznow()
    if incident.end_time:
        if incident.end_time <= now:
            duration = incident.end_time - incident.start_time
        else:
            duration = now - incident.start_time
    incident.duration = duration
    context = {
        "incident": incident,
        "page_title": str(incident),
        "autocreate_ticket": bool(get_ticket_plugin_path()),
    }
    return render(request, "htmx/incident/incident_detail.html", context=context)


def get_incident_ids_to_update(request):
    return request.POST.getlist("incident_ids", [])


def get_form_data(request, formclass: Optional[forms.Form]):
    formdata = request.POST or None
    cleaned_form = None
    if formclass and formdata:
        form = formclass(formdata)
        if form.is_valid():
            cleaned_form = form.cleaned_data
    return cleaned_form


@require_POST
def incident_update(request: HtmxHttpRequest, action: str):
    try:
        formclass, callback_func = INCIDENT_UPDATE_ACTIONS[action]
    except KeyError:
        LOG.error("Unrecognized action name %s when updating incidents.", action)
        return HttpResponseBadRequest("Invalid update action")
    incident_ids = get_incident_ids_to_update(request)
    formdata = get_form_data(request, formclass)
    if incident_ids:
        bulk_change_incidents(request.user, incident_ids, formdata, callback_func)
    return HttpResponseClientRefresh()


@require_GET
def filter_form(request: HtmxHttpRequest):
    request.session["selected_filter"] = None
    incident_list_filter = get_filter_function()
    filter_form, _ = incident_list_filter(request, None)
    context = {"filter_form": filter_form}
    return render(request, "htmx/incident/_incident_filterbox.html", context=context)


@require_POST
def create_filter(request: HtmxHttpRequest):
    from argus.htmx.incident.filter import create_named_filter

    filter_name = request.POST.get("filter_name", None)
    incident_list_filter = get_filter_function()
    filter_form, _ = incident_list_filter(request, None)
    if filter_name and filter_form.is_valid():
        filterblob = filter_form.to_filterblob()
        _, filter_obj = create_named_filter(request, filter_name, filterblob)
        if filter_obj:
            request.session["selected_filter"] = str(filter_obj.id)
            return HttpResponseClientRefresh()
    messages.error(request, "Failed to create filter")
    return HttpResponseBadRequest()


@require_POST
def delete_filter(request: HtmxHttpRequest, pk: int):
    filter_obj = get_object_or_404(Filter, id=pk)
    deleted_id = filter_obj.delete()
    if deleted_id:
        messages.success(request, f"Deleted filter {filter_obj.name}.")
        if request.session.get("selected_filter") == str(pk):
            request.session["selected_filter"] = None
        return HttpResponseClientRefresh()


@require_GET
def get_existing_filters(request: HtmxHttpRequest):
    existing_filters = Filter.objects.all().filter(user=request.user)
    if existing_filters:
        context = {"filters": existing_filters}
        return render(request, "htmx/incident/_existing_filters.html", context=context)
    else:
        return render(request, "htmx/incident/responses/empty_list_item.html", context={"message": "No filters found."})


@require_GET
def filter_select(request: HtmxHttpRequest):
    filter_id = request.GET.get("filter", None)
    if filter_id and get_object_or_404(Filter, id=filter_id):
        request.session["selected_filter"] = filter_id
        incident_list_filter = get_filter_function()
        filter_form, _ = incident_list_filter(request, None)
        context = {"filter_form": filter_form}
        return render(request, "htmx/incident/_incident_filterbox.html", context=context)
    else:
        request.session["selected_filter"] = None
        if request.htmx.trigger:
            return reswap(HttpResponse(), "none")
        else:
            return retarget(HttpResponse(), "#incident-filter-select")


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

    page_size, _ = get_or_update_preference(request, request.GET, "argus_htmx", "page_size")

    paginator = Paginator(object_list=qs, per_page=page_size)
    page_num = params.pop("page", "1")
    page = paginator.get_page(page_num)

    # The htmx magic - use a different, minimal base template for htmx
    # requests, allowing us to skip rendering the unchanging parts of the
    # template.
    if request.htmx:
        base_template = "htmx/incident/responses/_incident_list_refresh.html"
    else:
        base_template = "htmx/incident/_base.html"
    context = {
        "columns": columns,
        "filtered_count": filtered_count,
        "count": total_count,
        "filter_form": filter_form,
        "page_title": "Incidents",
        "base": base_template,
        "page": page,
        "last_refreshed": last_refreshed,
    }

    return render(request, "htmx/incident/incident_list.html", context=context)
