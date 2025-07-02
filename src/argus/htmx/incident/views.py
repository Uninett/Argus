from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Optional, Any

from django import forms
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.timezone import now as tznow
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseBadRequest, QueryDict
from django_htmx.http import HttpResponseClientRefresh, retarget

from argus.auth.utils import get_or_update_preference
from argus.htmx.incident.forms import IncidentListForm
from argus.incident.models import Incident
from argus.incident.ticket.utils import get_ticket_plugin_path
from argus.incident.ticket.base import TicketPluginException
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
    context = {
        "incident": incident,
        "page_title": str(incident),
        "autocreate_ticket": bool(get_ticket_plugin_path()),
    }
    return render(request, "htmx/incident/incident_detail.html", context=context)


def get_incident_ids_to_update(request):
    return request.POST.getlist("incident_ids", [])


def get_form(request, formclass: Optional[forms.Form]):
    formdata = request.POST or None
    form = None
    if formclass and formdata:
        form = formclass(formdata)
    return form


@require_POST
def incident_update(request: HtmxHttpRequest, action: str):
    try:
        formclass, callback_func = INCIDENT_UPDATE_ACTIONS[action]
    except KeyError:
        LOG.error("Unrecognized action name %s when updating incidents.", action)
        return HttpResponseBadRequest("Invalid update action")
    incident_ids = get_incident_ids_to_update(request)
    if not incident_ids:
        messages.warning(request, "No incidents selected, nothing to change")
        return HttpResponseClientRefresh()

    if action == "autocreate-ticket":
        try:
            single_autocreate_ticket_url_queryset(request, incident_ids, {"timestamp": tznow()})
        except TicketPluginException as e:
            messages.error(request, str(e))
        return HttpResponseClientRefresh()

    form = get_form(request, formclass)
    if form.is_valid():
        bulk_change_incidents(request, incident_ids, form.cleaned_data, callback_func)
    else:
        messages.error(request, form.errors)
    return HttpResponseClientRefresh()


@require_GET
def filter_form(request: HtmxHttpRequest):
    request.session["selected_filter"] = None
    incident_list_filter = get_filter_function()
    filter_form, _ = incident_list_filter(request, None)
    context = {"filter_form": filter_form}
    LOG.debug("filter_form view: GET: %s", request.GET)
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
def update_filter(request: HtmxHttpRequest, pk: int):
    filter_obj = get_object_or_404(Filter, id=pk)
    incident_list_filter = get_filter_function()
    filter_form, _ = incident_list_filter(request, None)
    if filter_form.is_valid():
        filterblob = filter_form.to_filterblob()
        filter_obj.filter = filterblob
        filter_obj.save()

        # Immediately select the newly updated filter - keep or not?
        # request.session["selected_filter"] = str(filter_obj.id)

        messages.success(request, f"Updated filter '{filter_obj.name}'.")
        return HttpResponseClientRefresh()
    messages.error(request, f"Failed to update filter '{filter_obj.name}'.")
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
        if request.htmx.target == "delete-filter-items":
            context.update({"action": "delete"})
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
            incident_list_filter = get_filter_function()
            filter_form, _ = incident_list_filter(request, None, use_empty_filter=True)
            context = {"filter_form": filter_form}
            return render(request, "htmx/incident/_incident_filterbox.html", context=context)
        else:
            return retarget(HttpResponse(), "#incident-filter-select")


def dedupe_querydict(querydict: QueryDict):
    # if in doubt, use the biggest hammer *sigh*
    qd = QueryDict(mutable=True)
    for key, value in querydict.items():
        value = querydict.getlist(key)  # value is always a list of strings
        value = filter(None, value)  # strip away empty strings
        value = list(set(value))  # dedupe list of strings
        if not value:
            continue
        qd.setlist(key, value)  # safely add to query dict
    qd._mutable = False  # make read only
    return qd


def add_param_to_querydict(querydict: QueryDict, key: str, value: Any):
    "Set key to value if missing from querydict"
    qd = querydict.copy()
    if value is None:
        return querydict
    if key not in qd:
        if isinstance(value, Iterable):
            if not value:
                return querydict
            if isinstance(value, str):
                value = [value]
            else:
                qd[key] = list(value)
        else:
            value = [str(value)]
        qd.setlist(key, value)
        qd._mutable = False
        return qd
    return querydict


@require_GET
def incident_list(request: HtmxHttpRequest) -> HttpResponse:
    LOG.debug("incident_list view: GET at start: %s", request.GET)
    request.GET = dedupe_querydict(request.GET)
    LOG.debug("incident_list view after dedupe: %s", request.GET)
    columns = get_incident_table_columns()

    # Load incidents
    qs = prefetch_incident_daughters().order_by("-start_time")
    total_count = qs.count()
    last_refreshed = make_aware(datetime.now())

    incident_list_filter = get_filter_function()
    filter_form, qs = incident_list_filter(request, qs)

    GET_params = {}
    if filter_form.is_bound:
        GET_params = filter_form.cleaned_data.copy()

    # Fetch timeframe from session since its GET parameter disappears
    _timeframe = int(request.session.get("timeframe", 0) or 0)
    if _timeframe:
        request.GET = add_param_to_querydict(request.GET, "timeframe", _timeframe)

    # non filterbox GET parameters
    GET_forms = {}
    for Form in IncidentListForm.__subclasses__():
        form = Form(request.GET)
        GET_forms[form.fieldname] = form
        GET_params[form.fieldname] = form.get_clean_value()
        qs = form.filter(qs)

    filtered_count = qs.count()

    if not request.session["timeframe"]:
        request.session["timeframe"] = GET_params["timeframe"]

    page_size, _ = get_or_update_preference(request, request.GET, "argus_htmx", "page_size")
    GET_params["page_size"] = page_size

    qd = QueryDict("").copy()
    qd.update(GET_params)
    LOG.debug("incident_list view: Cleaned QueryDict: %s", qd)
    request.GET = qd

    # Standard Django pagination
    paginator = Paginator(object_list=qs, per_page=page_size)
    page = paginator.get_page(GET_params.get("page", 1))
    last_page_num = page.paginator.num_pages

    refresh_info = {
        "count": total_count,
        "filtered_count": filtered_count,
        "last_refreshed": last_refreshed,
    }

    # The htmx magic - use a different, minimal base template for htmx
    # requests, allowing us to skip rendering the unchanging parts of the
    # template.
    if request.htmx:
        base_template = "htmx/incident/responses/_incident_list_refresh.html"
    else:
        base_template = "htmx/incident/_base.html"

    LOG.debug("incident_list view: GET at end: %s", request.GET)
    context = {
        "columns": columns,
        "filter_form": filter_form,
        "refresh_info": refresh_info,
        "refresh_info_forms": GET_forms,
        "page_title": "Incidents",
        "base": base_template,
        "page": page,
        "last_page_num": last_page_num,
        "second_to_last_page": last_page_num - 1,
    }
    return render(request, "htmx/incident/incident_list.html", context=context)
