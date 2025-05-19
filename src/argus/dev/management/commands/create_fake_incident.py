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
        parser.add_argument(
            "-s",
            "--source",
            type=str,
            help="Use this source for the incident (the source needs to exist, see 'create_source' for creating one)",
        )
        parser.add_argument("--stateless", action="store_true", help="Create a stateless incident (end_time = None)")
        parser.add_argument(
            "--file",
            type=lambda p: Path(p).absolute(),
            help="Path to json-file containing all data for the fake incident",
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

    def handle(self, *args, **options):
        if (file_path := options.get("file", "")) and any(options.get(name, None) for name in COMMAND_ARGUMENTS):
            raise CommandError("If argument 'file' is given no other arguments are allowed")

        content = {}
        if file_path:
            try:
                with file_path.open() as jsonfile:
                    content = json.load(jsonfile)
            except Exception as e:
                raise CommandError(e)
        else:
            content["tags"] = options.get("tags") or []
            content["description"] = options.get("description") or None
            content["source"] = options.get("source") or None
            content["batch_size"] = options.get("batch_size") or 1
            content["level"] = options.get("level") or None
            content["stateful"] = False if options.get("stateless") else True
            if metadata := options.get("metadata", "{}"):
                content["metadata"] = json.loads(metadata)
            if metadata_path := options.get("metadata_file", ""):
                try:
                    with metadata_path.open() as jsonfile:
                        content["metadata"] = json.load(jsonfile)
                except Exception as e:
                    raise CommandError(e)

        call_command("create_source", [content["source"], f"-t={content['source']}"])

        for i in range(content.pop("batch_size", 1)):
            try:
                create_fake_incident(**content)
            except (ValueError, ValidationError) as e:
                raise CommandError(str(e))
