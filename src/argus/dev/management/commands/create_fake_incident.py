import argparse
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.core.management.base import BaseCommand

from argus.incident.constants import Level
from argus.incident.models import create_fake_incident

User = get_user_model()


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

    def handle(self, *args, **options):
        tags = options.get("tags") or []
        description = options.get("description") or None
        source = options.get("source") or None
        source_type = options.get("source_type") or None
        batch_size = options.get("batch_size") or 1
        level = options.get("level") or None
        stateful = False if options.get("stateless") else True
        if metadata := options.get("metadata", "{}"):
            metadata = json.loads(metadata)
        if metadata_path := options.get("metadata_file", ""):
            if metadata_path:
                with metadata_path.open() as jsonfile:
                    metadata = json.load(jsonfile)
        if source:
            call_command("create_source", [source, f"-t={source_type or source}"])

        for i in range(batch_size):
            try:
                create_fake_incident(
                    tags=tags,
                    description=description,
                    source=source,
                    stateful=stateful,
                    level=level,
                    metadata=metadata,
                )
            except (ValueError, ValidationError) as e:
                raise CommandError(str(e))
