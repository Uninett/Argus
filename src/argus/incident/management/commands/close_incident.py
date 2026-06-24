import logging
from pathlib import Path
from typing import Optional

from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_duration

from argus.dev.utils import get_json_from_file
from argus.incident.models import Incident

COMMAND_ARGUMENTS = ["id", "source", "source_incident_id", "duration", "closing_message"]
LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Close one or multiple incidents"

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, help="Close the incident with the id <id>")
        parser.add_argument(
            "--source",
            type=str,
            help="Close the incident from the source <source>, needs source_incident_id to find the right incident",
        )
        parser.add_argument(
            "--source-incident-id",
            type=int,
            help="Close the incident with the id from the source system <source_incident_id>",
        )
        parser.add_argument(
            "--duration",
            type=str,
            help="Only close the incident after it has been open for the duration <duration>, duration should be in the format 'DD HH:MM:SS.uuuuuu'",
        )
        parser.add_argument(
            "--closing-message",
            type=str,
            help="Close the incident with the message <closing-message>",
        )
        parser.add_argument(
            "-f",
            "--files",
            nargs="+",
            type=str,
            help="List of paths to json-file containing all data needed to find the incidents that should be closed (id or source + source_incident_id) and optional duration",
        )

    def get_incident_data_from_arguments(self, options: dict) -> Optional[dict]:
        incident_data = {}
        incident_data["incident_id"] = options.get("id") or None
        incident_data["source"] = options.get("source") or None
        incident_data["source_incident_id"] = options.get("source_incident_id") or None
        incident_data["closing_message"] = options.get("closing_message") or ""

        if duration := options.get("duration"):
            try:
                incident_data["duration"] = parse_duration(duration)
            except ValueError:
                incident_data["duration"] = None
            if not incident_data.get("duration"):
                self.stderr.write(self.style.ERROR(f"Could not parse duration {duration}."))
                return
        else:
            incident_data["duration"] = None

        return incident_data

    def get_incident_data_from_file(self, file_path: str) -> Optional[dict]:
        file_content = get_json_from_file(base_command=self, file_path=Path(file_path).absolute())

        if not file_content:
            return None

        incident_data = {}
        incident_data["incident_id"] = file_content.get("id")
        incident_data["source"] = file_content.get("source")
        incident_data["source_incident_id"] = file_content.get("source_incident_id")
        incident_data["closing_message"] = file_content.get("closing_message", "")
        incident_data["file_path"] = file_path

        if duration := file_content.get("duration"):
            try:
                incident_data["duration"] = parse_duration(duration)
            except ValueError:
                incident_data["duration"] = None
            if not incident_data.get("duration"):
                self.stderr.write(self.style.ERROR(f"Could not parse duration {duration} from file {file_path}."))
                return
        else:
            incident_data["duration"] = None

        return incident_data

    def get_incident_qs(self, incident_data: dict) -> QuerySet:
        """Returns an incident queryset containing one incident described in the given incident data"""
        incident_qs = None
        if incident_data["incident_id"]:
            incident_qs = Incident.objects.filter(id=incident_data["incident_id"])
        # is not None is important here since 0 is a valid value for source_incident_id
        elif incident_data["source"] and incident_data["source_incident_id"] is not None:
            incident_qs = Incident.objects.filter(
                source__name=incident_data["source"], source_incident_id=incident_data["source_incident_id"]
            )
        return incident_qs

    def handle(self, *args, **options):
        if (file_paths := options.get("files", [])) and any(options.get(name, None) for name in COMMAND_ARGUMENTS):
            raise CommandError("If argument 'files' is given no other arguments are allowed")

        incident_list = []
        if file_paths:
            for file_path in file_paths:
                incident_list.append(self.get_incident_data_from_file(file_path))
        else:
            incident_list.append(self.get_incident_data_from_arguments(options))

        # Filter out None elements from list (e.g. file could not be found)
        incident_list = list(filter(None, incident_list))

        for incident_data in incident_list:
            incident_qs = self.get_incident_qs(incident_data)

            if not incident_qs or not incident_qs.exists():
                error = "Could not find incident"
                if incident_data.get("file_path"):
                    error += " from file " + incident_data.get("file_path")
                self.stderr.write(self.style.ERROR(error + "."))
                return

            incident = incident_qs.first()

            if incident.open and (
                not incident_data["duration"] or (timezone.now() - incident.start_time) >= incident_data["duration"]
            ):
                incident_qs.close(actor=incident.source.user, description=incident_data["closing_message"])
