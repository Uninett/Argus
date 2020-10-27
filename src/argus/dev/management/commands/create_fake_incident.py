from django.core.management.base import BaseCommand

from argus.incident.models import create_fake_incident


class Command(BaseCommand):
    help = "Create fake Incident"

    def add_arguments(self, parser):
        parser.add_argument("-t", "--tags", nargs="+", type=str, help="Add the listed tags to the incident")
        parser.add_argument("-d", "--description", type=str, help="Use this description for the incident")

    def handle(self, *args, **options):
        tags = options.get("tags", [])
        description = options.get("description", None)
        create_fake_incident(tags=tags, description=description)
