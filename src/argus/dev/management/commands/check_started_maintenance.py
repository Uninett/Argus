from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from argus.plannedmaintenance.models import PlannedMaintenanceTask


class Command(BaseCommand):
    help = "Find all planned maintenance tasks that have started recently and connect them with incidents that are hit by them"

    def add_arguments(self, parser):
        parser.add_argument(
            "-m",
            "--minutes",
            default=5,
            type=int,
            help="Only calculate the connected incidents for planned maintenance tasks that have started within the last <number> minutes",
        )

    def handle(self, *args, **options):
        start_time = timezone.now() - timedelta(minutes=options.get("minutes"))
        started_pm_tasks = PlannedMaintenanceTask.objects.started_after_time(start_time)

        for pm_task in started_pm_tasks:
            pm_task.connect_covered_incidents()
