from django.core.management.base import BaseCommand

from argus.incident.factories import SourceSystemFactory, SourceSystemTypeFactory


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
        sst = SourceSystemTypeFactory(name=source_type)
        ss = SourceSystemFactory(name=source, type=sst)
