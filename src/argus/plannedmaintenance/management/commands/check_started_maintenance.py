from django.core.management.base import BaseCommand

from argus.plannedmaintenance.models import PlannedMaintenanceTask


class Command(BaseCommand):
    help = "Find all current planned maintenance tasks and connect them with incidents that are hit by them"

    def handle(self, *args, **options):
        for pm_task in PlannedMaintenanceTask.objects.current():
            pm_task.connect_covered_incidents()
