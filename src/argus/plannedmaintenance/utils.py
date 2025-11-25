from typing import Optional

from argus.filter import get_filter_backend
from argus.incident.models import Event, IncidentQuerySet
from argus.plannedmaintenance.models import PlannedMaintenanceQuerySet, PlannedMaintenanceTask


filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter
FilterWrapper = filter_backend.FilterWrapper


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


def event_covered_by_planned_maintenance(event: Event, pm_tasks: Optional[PlannedMaintenanceQuerySet] = None) -> bool:
    """
    Returns true if the given event is covered by at least one of the given planned
    maintenance tasks
    """
    if not pm_tasks:
        pm_tasks = PlannedMaintenanceTask.objects.all()

    pm_tasks = pm_tasks.active_at_time(event.timestamp)

    for pm in pm_tasks:
        # Return true if all filters match that event
        covered = set()
        for filter in pm.filters.all():
            filter_wrapper = FilterWrapper(filterblob=filter.filter)
            covered.add(filter_wrapper.event_fits(event) and filter_wrapper.incident_fits(event.incident))
        if all(covered):
            return True
    return False
