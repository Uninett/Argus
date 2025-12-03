from django.core.management.base import BaseCommand
from django.db import transaction

from argus.auth.factories import SourceUserFactory
from argus.incident.factories import SourceSystemFactory, SourceSystemTypeFactory
from argus.incident.models import SourceSystem


class Command(BaseCommand):
    help = "Create new source, mainly for live testing"

    def add_arguments(self, parser):
        parser.add_argument("source", type=str, help="Create a source with name <source>, default type: argus")
        parser.add_argument(
            "-t", "--source-type", type=str, help="Create/use the source type <source-type> instead of argus"
        )

    def handle(self, *args, **options):
        source = options["source"]
        source_type = options.get("source_type") or "argus"
        if SourceSystem.objects.filter(name=source, type__name=source_type).exists():
            return
        with transaction.atomic():
            user = SourceUserFactory(username=source)
            sst = SourceSystemTypeFactory(name=source_type.lower())
            SourceSystemFactory(user=user, name=source, type=sst)
