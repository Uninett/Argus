from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from django.utils.timezone import now as tznow

from argus.filter import get_filter_backend
from argus.incident.models import Event, IncidentQuerySet
from argus.plannedmaintenance.models import PlannedMaintenanceQuerySet, PlannedMaintenanceTask

filter_backend = get_filter_backend()

if TYPE_CHECKING:
    from datetime import datetime

    from argus.incident.models import Incident

    FilterWrapper = filter_backend.FilterWrapper


QuerySetFilter = filter_backend.QuerySetFilter
PrecisionFilterWrapper = filter_backend.PrecisionFilterWrapper


class PlannedMaintenanceFilterWrapper(PrecisionFilterWrapper):
    def __init__(
        self,
        model: PlannedMaintenanceTask,
        filterwrapper: Optional[FilterWrapper] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Check a planned maintenance filter against an incident or an event

        Set timestamp in order to time travel/simulate what will happen. If
        timestamp is not set, it falls back to the time the wrapper was
        initiated.
        """
        self.model = model
        self.timestamp = timestamp if timestamp else tznow()
        super().__init__(model.filters, filterwrapper)

    def is_ongoing(self, timestamp: datetime):
        "Check whether the planned maintenance was ongoing at timestamp"

        # The equivalent of NotificationProfileFilterWrapper's model.active check
        return self.model.active_at_time(timestamp)

    def incident_fits(self, incident: Incident) -> bool:
        """Check if the incident fits

        Check that the the planned maintenance task is ongoing first, since it
        is cheaper, and bail out early if not.

        We can't check the start_time
        of the incident since it might start before the planned maintenance
        started but still be ongoing.
        """
        is_ongoing = self.is_ongoing(self.timestamp)
        if not is_ongoing:
            return False
        return super().incident_fits(incident)

    def event_fits(self, event: Event) -> bool:
        """Check if the event happened during the time covered by the pm

        No need to care about event types here, an ongoing pm silences all.
        """
        is_ongoing = self.is_ongoing(self.timestamp)
        event_fits = self.is_ongoing(event.timestamp)
        return is_ongoing and event_fits


def incidents_covered_by_planned_maintenance_task(
    queryset: IncidentQuerySet, pm_task: PlannedMaintenanceTask
) -> IncidentQuerySet:
    """
    Takes a queryset of incidents and a planned maintenance task and returns a queryset
    of incidents that are currently covered by that task
    """
    # Only if planned maintenance currently active
    if not pm_task.current:
        return queryset.none()

    # Only open incidents
    queryset = queryset.open()

    # All filters connected to this pm need to hit each incident
    for filter in pm_task.filters.all():
        queryset = QuerySetFilter.filtered_incidents(filter.filter, queryset)

    return queryset


def event_covered_by_planned_maintenance(
    event: Event, pm_tasks: Optional[PlannedMaintenanceQuerySet] = None, timestamp: Optional[datetime] = None
) -> bool:
    """
    Returns true if the given event is covered by at least one of the given planned
    maintenance tasks
    """
    if not pm_tasks:
        pm_tasks = PlannedMaintenanceTask.objects.all()

    for pm in pm_tasks:
        pmfw = PlannedMaintenanceFilterWrapper(pm, timestamp=timestamp)
        filter_fits = pmfw.filter_fits(event)
        # Abort early on first filter fit
        if filter_fits:
            return True
    return False
