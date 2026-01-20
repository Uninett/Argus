from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from argus.filter import get_filter_backend
from argus.incident.models import Event, Incident, IncidentQuerySet
from argus.plannedmaintenance.models import PlannedMaintenanceQuerySet, PlannedMaintenanceTask

filter_backend = get_filter_backend()

if TYPE_CHECKING:
    from datetime import datetime

    FilterWrapper = filter_backend.FilterWrapper


QuerySetFilter = filter_backend.QuerySetFilter
PrecisionFilterWrapper = filter_backend.PrecisionFilterWrapper


class PlannedMaintenanceFilterWrapper(PrecisionFilterWrapper):
    def __init__(
        self,
        model: PlannedMaintenanceTask,
        filterwrapper: Optional[FilterWrapper] = None,
    ):
        """Check a planned maintenance filter against an incident or an event

        Set timestamp in order to time travel/simulate what will happen. If
        timestamp is not set, it falls back to the time the wrapper was
        initiated.
        """
        self.model = model
        super().__init__(model.filters, filterwrapper)

    def is_ongoing(self, timestamp: datetime):
        "Check whether the planned maintenance was ongoing at timestamp"

        # The equivalent of NotificationProfileFilterWrapper's model.active check
        return self.model.active_at_time(timestamp)

    def event_fits(self, event: Event) -> bool:
        """Check if the event happened during the time covered by the pm

        No need to care about event types here, an ongoing pm silences all.
        """
        event_fits = self.is_ongoing(event.timestamp)
        return event_fits


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
        pmfw = PlannedMaintenanceFilterWrapper(pm)
        filter_fits = pmfw.filter_fits(event)
        # Abort early on first filter fit
        if filter_fits:
            return True
    return False


def connect_incident_with_planned_maintenance_tasks(
    incident: Incident, pm_tasks: Optional[PlannedMaintenanceQuerySet] = None
):
    """
    Connects the given incident with all open planned maintenance tasks that are
    covering it

    Does nothing for closed incidents
    """
    if not incident.open:
        return

    if not pm_tasks:
        pm_tasks = PlannedMaintenanceTask.objects.all()

    pm_tasks = pm_tasks.current().exclude(incidents__pk=incident.pk)

    for pm in pm_tasks:
        pmfw = PlannedMaintenanceFilterWrapper(pm)
        if pmfw.incident_fits(incident):
            pm.incidents.add(incident)
