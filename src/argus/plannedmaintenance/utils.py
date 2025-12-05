from __future__ import annotations

from typing import Optional, TYPE_CHECKING

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
        self.model = model
        self.timestamp = timestamp
        super().__init__(model.filters, filterwrapper)

    def is_ongoing(self, timestamp: datetime):
        return self.model.active_at_time(timestamp)

    def incident_fits(self, incident: Incident) -> bool:
        is_ongoing = self.is_ongoing(self.timestamp)
        if not is_ongoing:
            return False
        return super().incident_fits(incident)

    def event_fits(self, event: Event) -> bool:
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
