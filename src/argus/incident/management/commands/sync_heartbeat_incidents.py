from django.core.management.base import BaseCommand

from argus.incident.heartbeat_utils import sync_heartbeats_with_heartbeat_incidents


class Command(BaseCommand):
    help = "Check that heartbeat-supporting sources are alive"

    def handle(self, *args, **options):
        alive_sources, new_incidents = sync_heartbeats_with_heartbeat_incidents()
        if options["verbosity"] > 0:
            for source in alive_sources:
                self.stdout.write('Closed incident for source "{source.name}", it\'s back')
            for incident in new_incidents:
                self.stdout.write(f"Created incident {incident}")
        if new_incidents:
            count = len(new_incidents)
            self.stdout.write(f"Created {count} new incidents")
