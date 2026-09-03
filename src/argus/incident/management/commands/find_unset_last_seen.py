from django.core.management.base import BaseCommand

from argus.incident.models import SourceSystem, Event


def find_latest_event_by_heartbeatless_source():
    qs = SourceSystem.objects
    changes = []
    never_seen = []
    for source in qs.filter(last_seen__isnull=True).order_by("name"):
        try:
            event = Event.objects.filter(actor=source.user).only("received").latest("received")
        except Event.DoesNotExist:
            never_seen.append(source)
        else:
            changes.append((source, event.received))
    return changes, never_seen


class Command(BaseCommand):
    help = "Find timestamp of latest received events from sources with unset last_seen"

    def add_arguments(self, parser):
        parser.add_argument(
            "-s",
            "--save",
            action="store_true",
            help="Update last_seen with latest change",
        )

    def handle(self, *args, **options):
        changes, never_seen = find_latest_event_by_heartbeatless_source()

        if changes:
            if options["verbosity"]:
                self.stdout.write("Possibly dead sources:\n")
        for source, last_seen in changes:
            if options["verbosity"]:
                self.stdout.write(f"{source}: {last_seen}")
            if options["save"]:
                source.last_seen = last_seen
                source.save()

        if never_seen and options["verbosity"] > 0:
            if changes:
                self.stdout.write("")
            self.stdout.write("Never seen, never put into production?")
            self.stdout.write(", ".join(source.name for source in never_seen))
