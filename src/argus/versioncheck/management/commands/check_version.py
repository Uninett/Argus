from django.core.management.base import BaseCommand, CommandError

from argus.versioncheck.utils import VersionCheckError, fetch_latest_version_and_upload_time, register_version


class Command(BaseCommand):
    help = "Look for a new Argus version"

    def add_arguments(self, parser):
        parser.add_argument("-s", "--save", action="store_true", help="Save the new version to the database")

    def handle(self, *args, **options):
        try:
            latest_version, upload_time = fetch_latest_version_and_upload_time()
        except VersionCheckError as e:
            self.stderr.write(e)
            raise CommandError from e

        self.stdout.write(f"Latest version of Argus is: {latest_version}, uploaded {upload_time}")
        if options["save"]:
            versionobj, created = register_version(latest_version, upload_time)
            if created:
                self.stdout.write("Saved to database.")
            else:
                self.stdout.write("This version is already in the database.")
