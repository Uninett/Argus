import logging
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

from argus.incident.factories import create_stateful_incident
from argus.incident.models import HEARTBEAT_TAG, SOURCE_TAG_KEY, Incident, SourceSystem


LOG = logging.getLogger(__name__)
DEFAULT_FUDGE_FACTOR = 10
DEFAULT_LEVEL = 4
_FUDGE = timedelta(seconds=DEFAULT_FUDGE_FACTOR)

__all__ = [
    "sync_heartbeats_with_heartbeat_incidents",
]


def sync_heartbeats_with_heartbeat_incidents():
    timestamp = timezone.now()
    alive_sources = _close_incidents_whose_sources_are_alive_again(timestamp)
    new_incidents = _create_incidents_for_dead_sources(timestamp)
    return alive_sources, new_incidents


def _close_incidents_whose_sources_are_alive_again(timestamp):
    argus = SourceSystem.objects.get(name="argus")
    still_dead_sources = SourceSystem.objects.dead(timestamp - _FUDGE)
    outdated_incidents = Incident.objects.heartbeat_incidents().open()
    format_str = 'Source "{}" is again alive and well'
    sources = []
    for incident in outdated_incidents:
        source = incident.get_values_for_tag_key(SOURCE_TAG_KEY)
        if not source:
            LOG.error('Heartbeat incident "%s" is missing source-tag!', incident)
            continue
        elif len(source) > 1:
            LOG.error('Heartbeat incident "%s" has multiple source tags!?', incident)
            continue

        source_name = source[0]
        if still_dead_sources.filter(name=source_name).exists():
            continue

        try:
            source = SourceSystem.objects.get(name=source_name)
        except SourceSystem.DoesNotExist:
            LOG.error('Heartbeat source "%s" has disappeared!', incident)
            continue

        # phew, *now* we can close the incident
        incident.set_end(argus.user, timestamp, format_str.format(source))
        sources.append(source)
    return sources


def _create_incidents_for_dead_sources(timestamp: Optional[datetime] = None):
    # Create existing incidents whose sources have become dead
    dead_sources = SourceSystem.objects.dead(timestamp - _FUDGE)
    incident_owner = SourceSystem.objects.get(name="argus")
    # prevent multiple incidents
    heartbeat_incidents = Incident.objects.heartbeat_incidents().open()
    source_ids = (incident.source_id for incident in heartbeat_incidents)
    new_incidents = []
    for source in dead_sources.exclude(id__in=source_ids):
        incident = _get_or_create_incident_for_dead_source(source, incident_owner=incident_owner, timestamp=timestamp)
        if incident:
            new_incidents.append(incident)
    return new_incidents


def _get_or_create_incident_for_dead_source(
    source: SourceSystem,
    incident_owner: SourceSystem,
    timestamp: Optional[datetime] = None,
    level: int = DEFAULT_LEVEL,
):
    assert isinstance(source, SourceSystem), "source is not a SourceSystem"
    if not timestamp:
        timestamp = timezone.now()

    source_tag = f"{SOURCE_TAG_KEY}={source.name}"
    tags = [HEARTBEAT_TAG, source_tag]

    # One last check in case a heartbeat arrived in the meantime
    source.refresh_from_db()
    dead = source.is_dead(timestamp - _FUDGE)
    if dead:
        # prevent duplicates
        existing_incidents = Incident.objects.heartbeat_incidents().open().from_tags(source_tag)
        if existing_incidents.exists():
            try:
                return existing_incidents.get()
            except Incident.MultipleObjectsReturned:
                # TODO: fix, different function?
                LOG.error('Source "%s" has multiple open heartbeat incidents', source)
                return existing_incidents.first()
        # save new incident
        incident = create_stateful_incident(
            f"Missing heartbeat from source {source}, dead?",
            incident_owner,
            level,
            tags=tags,
            start_time=timestamp,
        )
        return incident
    return None
