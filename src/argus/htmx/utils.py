# Should be in argus proper and merged with api bulk actions
#
# THIS IS LESS DRY-ABLE THAN YOU (or SonarCloud) THINK(S)
#
# Uses composition, see bulk_change_incidents()

from typing import Any

from django.utils import timezone

from argus.incident.models import Incident
from argus.util.signals import bulk_changed


def send_changed_incidents(incidents):
    bulk_changed.send(sender=Incident, instances=incidents)


def get_qs_for_incident_ids(incident_ids: list[int], qs=None):
    # setup
    if qs is None:
        qs = Incident.objects.all()
    qs = qs.filter(pk__in=incident_ids)
    found_ids = set(qs.values_list("id", flat=True))

    # wash ids
    missing_ids = set(incident_ids) - found_ids
    return qs, missing_ids


def bulk_ack_queryset(actor, qs, data: dict[str, Any]):
    timestamp = data["timestamp"]
    description = data.get("description", "")
    expiration = data.get("expiration", None)
    acks = qs.create_acks(actor, timestamp, description, expiration)
    incidents = []
    for ack in acks:
        incidents.append(ack.event.incident)
    return incidents


def bulk_close_queryset(actor, qs, data: dict[str, Any]):
    timestamp = data["timestamp"]
    description = data.get("description", "")
    events = qs.close(actor, timestamp, description)
    incidents = []
    for event in events:
        incidents.append(event.incident)
    return incidents


def bulk_reopen_queryset(actor, qs, data: dict[str, Any]):
    timestamp = data["timestamp"]
    description = data.get("description", "")
    events = qs.reopen(actor, timestamp, description)
    incidents = []
    for event in events:
        incidents.append(event.incident)
    return incidents


def bulk_change_ticket_url_queryset(actor, qs, data: dict[str, Any]):
    timestamp = data["timestamp"]
    ticket_url = data.get("ticket_url", "")
    return qs.update_ticket_url(actor, ticket_url, timestamp=timestamp)


def bulk_change_incidents(actor, incident_ids: list[int], data: dict[str, Any], func, qs=None):
    """
    Update incidents in bulk

    Applies ``func`` to the incidents in ``incident_ids`` with the
    pre-validated bulk-type dependent key-value pairs in ``data``. Blames it on
    the user ``actor``. Adds ``timestamp`` to ``data`` if it is not already present.

    Returns a queryset of the changed incidents and a list of incident ids that
    could not be changed due to for instance

    - The incidents have been deleted in the meantime
    - We're working on a subset of incidents and the ids are not in that subset
    """
    qs, missing_ids = get_qs_for_incident_ids(incident_ids, qs)
    if not data.get("timestamp"):
        data["timestamp"] = timezone.now()
    incidents = func(actor, qs, data)
    send_changed_incidents(incidents)
    return incidents, missing_ids
