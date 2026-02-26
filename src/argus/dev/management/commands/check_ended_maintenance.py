import logging
from datetime import timedelta
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from argus.plannedmaintenance.models import PlannedMaintenanceTask


LOG = logging.getLogger(__name__)


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
        if not getattr(settings, "ENABLE_CRON_JOBS", False):
            sys.exit()
        end_time = timezone.now() - timedelta(minutes=options.get("minutes"))
        ended_pm_tasks = PlannedMaintenanceTask.objects.ended_after_time(end_time)
        if count := ended_pm_tasks.count():
            LOG.info("Cleaning up after %s ended planned maintenance tasks", count)
        else:
            LOG.info("No planned maintenance tasks to clean up after")

        for pm_task in ended_pm_tasks:
            pm_task.incidents.clear()
        else:
            LOG.info("Finished cleaning up after ended planned maintenance tasks")
