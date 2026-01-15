from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from argus.plannedmaintenance.models import PlannedMaintenanceTask


class Command(BaseCommand):
    help = "Find all planned maintenance tasks that have ended recently and remove the incidents connection"

    def add_arguments(self, parser):
        parser.add_argument(
            "-m",
            "--minutes",
            default=5,
            type=int,
            help="Only remove the incidents from the planned maintenance tasks that have ended within the last <number> minutes",
        )

    def handle(self, *args, **options):
        end_time = timezone.now() - timedelta(minutes=options.get("minutes"))
        ended_pm_tasks = PlannedMaintenanceTask.objects.ended_after_time(end_time)

        for pm_task in ended_pm_tasks:
            pm_task.incidents.clear()
