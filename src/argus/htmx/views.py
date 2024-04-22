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


def incident(request, pk: int):
    incident = get_object_or_404(id=pk)
    context = {"incident": incident}
    return render(request, "htmx/incidents/detail.html", context=context)


#
# incident.tags.key
