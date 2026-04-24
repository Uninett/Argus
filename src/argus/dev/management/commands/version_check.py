from django.core.management.base import BaseCommand

from argus.versioncheck.models import LastSeenVersion
from argus.versioncheck.tasks import get_latest_version


class Command(BaseCommand):
    help = "Look for a new Argus version"

    def add_arguments(self, parser):
        parser.add_argument("-s", "--save", action="store_true", help="Save the new version to the database")

    def handle(self, *args, **options):
        latest_version = get_latest_version()
        self.stdout.write(f"Latest version of Argus is: {latest_version}")
        if options["save"]:
            _, created = LastSeenVersion.objects.get_or_create(version=latest_version)
            if created:
                self.stdout.write("Saved to database.")
            else:
                self.stdout.write("This version is already in the database.")
