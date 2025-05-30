import argparse
import json
import logging
from pathlib import Path
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.core.management.base import BaseCommand

from argus.dev.utils import get_json_from_file
from argus.incident.constants import Level
from argus.incident.models import create_fake_incident

LOG = logging.getLogger(__name__)
User = get_user_model()

COMMAND_ARGUMENTS = [
    "tags",
    "description",
    "source",
    "batch_size",
    "level",
    "stateful",
    "metadata",
    "metadata_path",
]


class Range(argparse.Action):
    def __init__(self, minimum=None, maximum=None, *args, **kwargs):
        self.min = minimum
        self.max = maximum
        kwargs["metavar"] = "[%d-%d]" % (self.min, self.max)
        super(Range, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        if not (self.min <= value <= self.max):
            msg = "invalid choice: %r (choose from [%d-%d])" % (value, self.min, self.max)
            raise argparse.ArgumentError(self, msg)
        setattr(namespace, self.dest, value)


class Command(BaseCommand):
    help = "Create fake Incident"

    def add_arguments(self, parser):
        parser.add_argument("-b", "--batch-size", type=int, help="Create <batch size> incidents in one go")
        parser.add_argument("-d", "--description", type=str, help="Use this description for the incident")
        parser.add_argument(
            "-l",
            "--level",
            type=int,
            action=Range,
            minimum=min(Level).value,
            maximum=max(Level).value,
            default=0,
            help="Set level to <level>, otherwise a random number within the correct range is used",
        )
        parser.add_argument("-t", "--tags", nargs="+", type=str, help="Add the listed tags to the incident")
        parser.add_argument("-s", "--source", type=str, help="Use this source for the incident")
        parser.add_argument("--source-type", type=str, help="Use this source type for the incident")
        parser.add_argument("--stateless", action="store_true", help="Create a stateless incident (end_time = None)")
        parser.add_argument(
            "--files",
            nargs="+",
            type=str,
            help="List of paths to json-files containing all data for the fake incidents",
        )

        metadata_parser = parser.add_mutually_exclusive_group()
        metadata_parser.add_argument(
            "--metadata",
            type=str,
            help="Store json in the metadata field",
        )
        metadata_parser.add_argument(
            "--metadata-file",
            type=lambda p: Path(p).absolute(),
            help="Path to json-file to store in the metadata field",
        )

    def get_content_from_arguments(self, options: dict) -> Optional[dict]:
        content = {}
        content["tags"] = options.get("tags") or []
        content["description"] = options.get("description") or None
        content["source"] = options.get("source") or None
        content["source_type"] = options.get("source_type") or None
        content["batch_size"] = options.get("batch_size") or 1
        content["level"] = options.get("level") or None
        content["stateful"] = False if options.get("stateless") else True
        if metadata := options.get("metadata", "{}"):
            try:
                content["metadata"] = json.loads(metadata)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                self.stderr.write(self.style.ERROR(e))
        if metadata_path := options.get("metadata_file", ""):
            content["metadata"] = get_json_from_file(self, metadata_path)
        if (metadata or metadata_path) and not content["metadata"]:
            return

        return content

    def handle(self, *args, **options):
        if (file_paths := options.get("files", "")) and any(options.get(name, None) for name in COMMAND_ARGUMENTS):
            raise CommandError("If argument 'files' is given no other arguments are allowed")

        incident_contents = []
        if file_paths:
            incident_contents = list(
                filter(None, [get_json_from_file(self, Path(file_path).absolute()) for file_path in file_paths])
            )
        else:
            incident_contents = list(filter(None, [self.get_content_from_arguments(options=options)]))
            if incident_contents and (batch_size := incident_contents[0].pop("batch_size", 1)) > 1:
                incident_contents *= batch_size

        if not incident_contents:
            return

        for incident in incident_contents:
            if source := incident.get("source"):
                call_command("create_source", [source, f"-t={incident.get('source_type') or source}"])

            try:
                create_fake_incident(**incident)
            except (ValueError, ValidationError) as e:
                self.stderr.write(self.style.ERROR(str(e)))
