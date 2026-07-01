from django.core.management.base import BaseCommand

from argus.incident.heartbeat_utils import sync_heartbeats_with_heartbeat_incidents


class Command(BaseCommand):
    help = "Check that heartbeat-supporting sources are alive"

    def handle(self, *args, **options):
        alive_sources, new_incidents = sync_heartbeats_with_heartbeat_incidents()
        if not (alive_sources or new_incidents):
            return
        if options["verbosity"] > 0:
            for source in alive_sources:
                self.stdout.write(f'Closed incident for source "{source.name}", it\'s back')
            for incident in new_incidents:
                self.stdout.write(f"Created incident {incident}")
        else:
            count_incidents = len(new_incidents)
            self.stdout.write(f"Created {count_incidents} new incidents")
            count_alive = len(alive_sources)
            self.stdout.write(f"Closed {count_alive} existing incidents")
