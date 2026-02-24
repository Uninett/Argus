from __future__ import annotations

from typing import TYPE_CHECKING

from argus.plannedmaintenance.utils import connect_incident_with_planned_maintenance_tasks

if TYPE_CHECKING:
    from argus.incident.models import Incident


def add_planned_maintenance_tasks_covering_incident(instance: Incident, **kwargs):
    connect_incident_with_planned_maintenance_tasks(incident=instance)
