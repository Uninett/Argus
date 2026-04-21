from django.core.management.base import BaseCommand

from argus.plannedmaintenance.models import PlannedMaintenanceTask


class Command(BaseCommand):
    help = "Find all current and future planned maintenance tasks and connect them with incidents that are hit by them"

    def handle(self, *args, **options):
        current_pm_tasks = PlannedMaintenanceTask.objects.current()
        future_pm_tasks = PlannedMaintenanceTask.objects.future()

        for pm_task in current_pm_tasks.union(future_pm_tasks):
            pm_task.connect_covered_incidents()
