import sys

from django.core.management.base import BaseCommand

from argus.notificationprofile.media import sync_media


class Command(BaseCommand):
    # Cannot be a data migration because the content are controlled by a django setting
    help = "Sync media"

    def handle(self, *args, **options):
        sync_media()
