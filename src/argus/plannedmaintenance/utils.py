from argus.filter import get_filter_backend
from argus.incident.models import IncidentQuerySet
from argus.plannedmaintenance.models import PlannedMaintenanceTask


filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter


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
