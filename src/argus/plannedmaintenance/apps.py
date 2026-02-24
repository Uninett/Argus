from django.apps import AppConfig
from django.db.models.signals import post_save


class PlannedmaintenanceConfig(AppConfig):
    name = "argus.plannedmaintenance"
    label = "argus_plannedmaintenance"

    def ready(self):
        from .signals import add_planned_maintenance_tasks_covering_incident

        post_save.connect(add_planned_maintenance_tasks_covering_incident, "argus_incident.Incident")
