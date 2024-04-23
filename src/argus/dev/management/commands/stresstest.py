from httpx import TimeoutException, HTTPStatusError, HTTPError

from django.core.management.base import BaseCommand

from argus.dev.utils import StressTester, DatabaseMismatchError


class Command(BaseCommand):
    help = "Stresstests incident creation API"

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            type=str,
            help="URL for target argus host. Port may be specified (defaults to 443 for HTTPS and 80 for HTTP), e.g. https://argushost.no:8080",
        )
        parser.add_argument(
            "token",
            type=str,
            help="Token for authenticating against target API. The token must belong to a user that is associated with a source system",
        )
        parser.add_argument(
            "-s",
            "--seconds",
            type=int,
            help="Number of seconds to send http requests. After this no more requests will be sent but responses will be waited for. Default 10s",
            default=10,
        )
        parser.add_argument("-t", "--timeout", type=int, help="Timeout for requests. Default 5s", default=5)
        parser.add_argument("-w", "--workers", type=int, help="Number of workers. Default 1", default=1)
        parser.add_argument("-b", "--bulk", action="store_true", help="Bulk ACK created incidents")

    def handle(self, *args, **options):
        tester = StressTester(options.get("url"), options.get("token"), options.get("timeout"), options.get("workers"))
        try:
            self.stdout.write("Running stresstest ...")
            incident_ids, runtime = tester.run(options.get("seconds"))
            requests_per_second = round(len(incident_ids) / runtime.total_seconds(), 2)
            self.stdout.write("Verifying incidents were created correctly ...")
            tester.verify(incident_ids)
            if options.get("bulk"):
                self.stdout.write("Bulk ACKing incidents ...")
                tester.bulk_ack(incident_ids)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Stresstest completed. Runtime: {runtime}. Incidents created: {len(incident_ids)}. Average incidents per second: {requests_per_second}."
                )
            )
        except (DatabaseMismatchError, HTTPStatusError, TimeoutException) as e:
            self.stderr.write(self.style.ERROR(e))
        except HTTPError as e:
            self.stderr.write(self.style.ERROR(f"HTTP Error: {e}"))
