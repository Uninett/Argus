import json
import logging
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.utils import timezone

from argus.notificationprofile.models import Filter
from argus.plannedmaintenance.models import PlannedMaintenanceTask

LOG = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Create planned maintenance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--created_by", type=str, help="Login of the user this PM should be associated with, default type: argus"
        )
        parser.add_argument(
            "--start_time",
            type=str,
            help="Start time of the PM, example for format: 2026-11-05 12:52:22.349734+00:00, default: now",
        )
        parser.add_argument(
            "--end_time",
            type=str,
            help="End time of the PM, default: none",
        )
        parser.add_argument(
            "-d", "--description", type=str, help="A description of what the PM covers or why it exists"
        )

        filter_parser = parser.add_mutually_exclusive_group()
        filter_parser.add_argument(
            "--filter_blob",
            type=str,
            help="Create a new filter with the following filterblob, name of the new filter needs to be part of the filterblob",
        )
        filter_parser.add_argument(
            "--filter_ids", type=int, nargs="+", help="Add the filters with the given ids to the PM task"
        )

    def get_content_from_arguments(self, options: dict) -> Optional[dict]:
        content = {}
        username = options.get("created_by") or "argus"
        try:
            content["created_by"] = User.objects.get(username=username)
        except User.DoesNotExist as e:
            self.stderr.write(self.style.ERROR("created_by: " + str(e)))
            return
        content["start_time"] = options.get("start_time") or timezone.now()
        if end_time := options.get("end_time"):
            content["end_time"] = end_time
        content["description"] = options.get("description") or ""
        if filter_blob := options.get("filter_blob", "{}"):
            try:
                content["filter_blob"] = json.loads(filter_blob)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                self.stderr.write(self.style.ERROR("filter_blob: " + str(e)))
                return
        if filter_ids := options.get("filter_ids", ""):
            content["filter_ids"] = filter_ids
        if not (filter_blob or filter_ids):
            self.stderr.write(self.style.ERROR("A planned maintenance task without a filter does nothing"))
            return

        return content

    def handle(self, *args, **options):
        pm_contents = self.get_content_from_arguments(options=options)

        if not pm_contents:
            return

        filter_ids = pm_contents.pop("filter_ids", None)
        if not filter_ids:
            filter_blob = pm_contents.pop("filter_blob")
            name = filter_blob.pop("name", None)
            if not name:
                self.stderr.write(self.style.ERROR("Cannot create a new filter without a name"))
                return
            try:
                filter_from_blob = Filter.objects.create(user=pm_contents["created_by"], name=name, filter=filter_blob)
                filter_ids = [filter_from_blob.pk]
            except (IntegrityError, ValueError, ValidationError) as e:
                self.stderr.write(self.style.ERROR(str(e)))

        try:
            pm = PlannedMaintenanceTask.objects.create(**pm_contents)
            pm.filters.add(*filter_ids)
        except (IntegrityError, ValueError, ValidationError) as e:
            self.stderr.write(self.style.ERROR(str(e)))
