from django.core.management.base import BaseCommand

from argus.incident.models import create_fake_incident


class Command(BaseCommand):
    help = "Create fake Incident"

    def add_arguments(self, parser):
        parser.add_argument("-t", "--tags", nargs="+", type=str, help="Add the listed tags to the incident")
        parser.add_argument("-b", "--batch-size", type=int, help="Create <batch size> incidents in one go")
        parser.add_argument("-d", "--description", type=str, help="Use this description for the incident")
        parser.add_argument("--stateless", action="store_true", help="Create a stateless incident (end_time = None)")

    def handle(self, *args, **options):
        tags = options.get("tags") or []
        description = options.get("description") or None
        batch_size = options.get("batch_size") or 1
        stateful = False if options.get("stateless") else True
        for i in range(batch_size):
            create_fake_incident(tags=tags, description=description, stateful=stateful)
