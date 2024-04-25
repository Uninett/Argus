import logging

from django.conf import settings
from django.shortcuts import render, reverse, get_object_or_404

from argus.incident.models import Incident

LOG = logging.getLogger(__name__)


def incidents(request):
    qs = Incident.objects.all().order_by("-start_time")
    latest = qs.latest("start_time").start_time
    context = {
        "qs": qs,
        "latest": latest,
        "page_title": "Incidents",
    }
    return render(request, "htmx/incidents/list.html", context=context)


# fetch with htmx
def incident_row(request, pk: int):
    incident = get_object_or_404(Incident, d=pk)
    context = {"incident": incident}
    return render(request, "htmx/incidents/_incident_row.html", context=context)


def incident_detail(request, pk: int):
    incident = get_object_or_404(Incident, id=pk)
    context = {
        "incident": incident,
        "page_title": str(incident),
    }
    return render(request, "htmx/incidents/incident_detail.html", context=context)


#
# incident.tags.key
