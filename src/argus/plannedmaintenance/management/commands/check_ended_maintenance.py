from django.core.management.base import BaseCommand

from argus.plannedmaintenance.models import PlannedMaintenanceTask


class Command(BaseCommand):
    help = "Removes incidents from ended planned maintenance tasks"

    def handle(self, *args, **options):
        ended_pm_tasks_with_linked_incidents = PlannedMaintenanceTask.objects.past().exclude(incidents=None)

        for pm_task in ended_pm_tasks_with_linked_incidents:
            pm_task.incidents.clear()
