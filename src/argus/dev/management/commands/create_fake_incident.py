import argparse
from random import randint

from django.core.management.base import BaseCommand

from argus.incident.constants import MIN_INCIDENT_LEVEL, MAX_INCIDENT_LEVEL
from argus.incident.models import create_fake_incident


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
            minimum=MIN_INCIDENT_LEVEL,
            maximum=MAX_INCIDENT_LEVEL,
            default=0,
            help="Set level to <level>, otherwise a random number within the correct range is used",
        )
        parser.add_argument("-t", "--tags", nargs="+", type=str, help="Add the listed tags to the incident")
        parser.add_argument("--stateless", action="store_true", help="Create a stateless incident (end_time = None)")

    def handle(self, *args, **options):
        tags = options.get("tags") or []
        description = options.get("description") or None
        batch_size = options.get("batch_size") or 1
        level = options.get("level") or None
        stateful = False if options.get("stateless") else True
        for i in range(batch_size):
            create_fake_incident(tags=tags, description=description, stateful=stateful, level=level)
