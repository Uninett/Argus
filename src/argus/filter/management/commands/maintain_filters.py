from django.core.management.base import BaseCommand, CommandError

from argus.filter import get_filter_backend
from argus.notificationprofile.models import Filter


filter_backend = get_filter_backend()


class Command(BaseCommand):
    help = "Clean existing filters: convert to newest standard"

    def add_arguments(self, parser):
        parser.add_argument(
            "-n",
            "--dry-run",
            action="store_true",
            help="Show filters that need cleaning",
        )

    def handle(self, *args, **options):
        try:
            minimalize_filterblob = filter_backend.minimalize_filterblob
        except AttributeError:
            msg = 'Filter backend does not include "minimalize_filterblob", aborting'
            raise CommandError(msg)

        if options["verbosity"]:
            self.stdout.write("Name	User id	Before	After")

        for filter in Filter.objects.order_by("user").exclude(filter={}):
            old_filter = filter.filter
            cleaned_filter = minimalize_filterblob(old_filter)

            if old_filter == cleaned_filter:
                continue

            if options["verbosity"]:
                self.stdout.write(f"{filter.user_id}	{filter.name}	{old_filter}	{cleaned_filter}")

            if not options["dry_run"]:
                filter.filter = cleaned_filter
                filter.save()
