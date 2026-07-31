import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from django.utils import timezone

from argus.incident.factories import create_stateful_incident
from argus.incident.models import HEARTBEAT_TAG, SOURCE_TAG_KEY, Incident, SourceSystem


LOG = logging.getLogger(__name__)
DEFAULT_FUDGE_FACTOR = 10
DEFAULT_LEVEL = 4
HEARTBEAT_FUDGE = timedelta(seconds=DEFAULT_FUDGE_FACTOR)
INCIDENT_DESCRIPTION_TEMPLATE = "Missing heartbeat from source {source}, dead?"

__all__ = [
    "sync_heartbeats_with_heartbeat_incidents",
]


def sync_heartbeats_with_heartbeat_incidents() -> Tuple[List[SourceSystem], List[Incident], List[Incident]]:
    """Sync heartbeat-configured sources with heartbeat incidents

    Returns a list of no longer dead sources, freshly created incidents, and
    incidents for sources that are still dead.
    """
    timestamp = timezone.now()
    alive_sources, closed_incidents, remaining_incidents = _close_heartbeat_incidents(timestamp)
    new_incidents, existing_incidents = _create_incidents_for_dead_sources(timestamp)
    remaining_incidents = list(set(remaining_incidents + existing_incidents))
    return alive_sources, new_incidents, remaining_incidents


def _close_heartbeat_incidents(timestamp: datetime) -> Tuple[List[SourceSystem], List[Incident], List[Incident]]:
    """Close all existing heartbeat incidents that can be closed

    Returns a list of reanimated sources followed by a list of freshly
    created incidents and finally a list of incidents that could not be closed.
    """
    outdated_incidents = Incident.objects.heartbeat_incidents().open()
    sources = []
    closed_incidents = []
    remaining_incidents = []
    for incident in outdated_incidents:
        source, incident = _attempt_closing_heartbeat_incident(incident, timestamp)
        if source:
            sources.append(source)
        if incident.open:
            remaining_incidents.append(incident)
        else:
            closed_incidents.append(incident)
    return sources, closed_incidents, remaining_incidents


def _attempt_closing_heartbeat_incident(
    incident: Incident, timestamp: datetime
) -> Tuple[Optional[SourceSystem], Incident]:
    """Try to close a heartbeat incident

    - If the source is alive again, return both the source and the closed
      incident.
    - If the source is still dead, return None and the still open incident.

    If something was wrong with the source or incident, an error is logged.

    - If the source has disappeared return None and the force-closed incident.
    - If the incident is missing its source tag return None and the
      force-closed incident.
    - If the incident has multiple source tags, return None and the still open
      incident.[*]

    [*] This should never happen but is included for completeness.
    """
    argus = SourceSystem.objects.get(name="argus")
    alive_description = 'Source "{}" is again alive and well'
    missing_tag_description = "The source tag of incident {} is missing, closing"
    missing_source_description = "The source of incident {} is gone, closing"

    source_ids = incident.get_values_for_tag_key(SOURCE_TAG_KEY)
    # We need exactly one source-tag.
    # We don't need to check for multiple *identical* tags,
    # that's a UniqueError, but we should also only have one source-tag
    if not source_ids:
        LOG.error('Heartbeat incident "%s" is missing source-tag!', incident.id)
        incident.set_end(argus.user, timestamp, missing_tag_description.format(incident.id))
        return None, incident
    elif len(source_ids) > 1:  # WAT, inconceivable
        LOG.error('Heartbeat incident "%s" has multiple source tags!?', incident.id)
        return None, incident

    source_id = source_ids[0]
    try:
        source = SourceSystem.objects.get(pk=source_id)
    except SourceSystem.DoesNotExist:
        LOG.error('Heartbeat source "%s" has disappeared!', source_id)
        incident.set_end(argus.user, timestamp, missing_source_description.format(incident.id))
        return None, incident

    if source.is_dead(timestamp - HEARTBEAT_FUDGE):
        return None, incident

    # phew, *now* we can close the incident
    incident.set_end(argus.user, timestamp, alive_description.format(source))
    return source, incident


def _create_incidents_for_dead_sources(timestamp: Optional[datetime] = None) -> tuple[list[Incident], list[Incident]]:
    """
    Creates heartbeat incidents for dead sources as of TIMESTAMP

    Keeps track of freshly created incidents versus already existing incidents.
    """
    # Create existing incidents whose sources have become dead
    dead_sources = SourceSystem.objects.dead(timestamp - HEARTBEAT_FUDGE)
    incident_owner = SourceSystem.objects.get(name="argus")
    # prevent multiple incidents
    heartbeat_incidents = Incident.objects.heartbeat_incidents().open()
    source_ids = (incident.source_id for incident in heartbeat_incidents)
    new_incidents = []
    existing_incidents = []
    for source in dead_sources.exclude(id__in=source_ids):
        incident, new = _get_or_create_incident_for_dead_source(
            source, incident_owner=incident_owner, timestamp=timestamp
        )
        if incident:
            if new:
                new_incidents.append(incident)
            else:
                existing_incidents.append(incident)
    return new_incidents, existing_incidents


def _get_or_create_incident_for_dead_source(
    source: SourceSystem,
    incident_owner: SourceSystem,
    timestamp: Optional[datetime] = None,
    level: int = DEFAULT_LEVEL,
) -> Tuple[Optional[Incident], Optional[bool]]:
    """
    Create a heartbeat incident for one specific dead source

    If the source is actually dead, returns the incident and whether it was
    freshly created (True) or not (False).

    Logs if there are multiple incidents for the source, and returns one of the
    incidents and that it was not freshly created (False).

    If the source is actually alive, returns (None, None)
    """
    assert isinstance(source, SourceSystem), "source is not a SourceSystem"
    if not timestamp:
        timestamp = timezone.now()

    source_tag = f"{SOURCE_TAG_KEY}={source.pk}"
    tags = [HEARTBEAT_TAG, source_tag]

    # One last check in case a heartbeat arrived in the meantime
    source.refresh_from_db()
    dead = source.is_dead(timestamp - HEARTBEAT_FUDGE)
    if dead:
        # prevent duplicates
        existing_incidents = Incident.objects.heartbeat_incidents().open().from_tags(source_tag)
        if existing_incidents.exists():
            try:
                return existing_incidents.get(), False
            except Incident.MultipleObjectsReturned:
                LOG.error('Source "%s" has multiple open heartbeat incidents', source)
                return existing_incidents.first(), False
        # save new incident
        incident = create_stateful_incident(
            INCIDENT_DESCRIPTION_TEMPLATE.format(source=str(source)),
            incident_owner,
            level,
            tags=tags,
            start_time=timestamp,
        )
        return incident, True
    return None, None
