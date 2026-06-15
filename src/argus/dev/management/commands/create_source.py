from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction

from argus.auth.factories import SourceUserFactory
from argus.incident.factories import SourceSystemFactory
from argus.incident.models import SourceSystem, create_source


class Command(BaseCommand):
    help = "Create new source, mainly for live testing"

    def add_arguments(self, parser):
        parser.add_argument("source", type=str, help="Create a source with name <source>, default type: argus")
        parser.add_argument(
            "-t", "--source-type", type=str, help="Create/use the source type <source-type> instead of argus"
        )
        base_url = parser.add_mutually_exclusive_group()
        base_url.add_argument(
            "--base-url", dest="base_url", type=str, help="Use as the base url for links into the source system"
        )
        base_url.add_argument(
            "--no-base-url", dest="base_url", action="store_const", const="", help="Let the base_url field be empty"
        )
        base_url.add_argument(
            "--fake-base-url", action="store_true", help="Generate a random link suitable for base_url"
        )

    def handle(self, *args, **options):
        source = options["source"]
        source_type = options.get("source_type") or "argus"
        if SourceSystem.objects.filter(name=source, type__name=source_type).exists():
            return
        if options.get("fake-base-url", False):
            base_url = None
        else:
            base_url = options["base_url"]

        ss = create_source(source, source_type, base_url)

        if options["verbosity"]:
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully created source "%s" with id %s' % (ss.name, ss.pk),
                )
            )
