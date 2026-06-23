import sys

from django.core.management.base import BaseCommand

from argus.notificationprofile.media import sync_media


class Command(BaseCommand):
    help = "Sync anything needing syncing that is not covered by migrate"

    def add_arguments(self, parser):
        parser.add_argument("-l", "--list", action="store_true", help="Show the available syncs that will be run")

    def handle(self, *args, **options):
        if options.get("list", False):
            sys.stdout.write("Sync MEDIA_PLUGINS setting to MEDIA table")
            sys.exit(0)

        sync_media()
