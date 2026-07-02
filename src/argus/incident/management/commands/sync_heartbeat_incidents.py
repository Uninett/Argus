from django.core.management.base import BaseCommand

from argus.incident.heartbeat_utils import sync_heartbeats_with_heartbeat_incidents


class Command(BaseCommand):
    help = "Check that heartbeat-supporting sources are alive"

    def handle(self, *args, **options):
        alive_sources, new_incidents, remaining_incidents = sync_heartbeats_with_heartbeat_incidents()
        if not (alive_sources or new_incidents or remaining_incidents):
            return
        count_closed = len(alive_sources)
        count_incidents = len(new_incidents)
        count_dead = len(remaining_incidents)

        if options["verbosity"] > 0:
            self.stdout.write(
                f"Heartbeat incidents: Created: {count_incidents}, Closed: {count_closed}, Remaining: {count_dead}"
            )

        if options["verbosity"] > 1:
            if count_incidents:
                self.stdout.write()
                self.stdout.write("Created incidents:")
                for incident in new_incidents:
                    self.stdout.write(f"- {incident}")

            if count_closed:
                self.stdout.write()
                self.stdout.write("Closed incidents:")
                for source in alive_sources:
                    self.stdout.write(f"- {source.name}")

            if count_dead:
                self.stdout.write()
                self.stdout.write("Remaining incidents:")
                for incident in remaining_incidents:
                    self.stdout.write(f"- {incident}")
