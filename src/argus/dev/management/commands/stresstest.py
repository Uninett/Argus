from datetime import datetime, timedelta
from urllib.parse import urljoin
import asyncio
import itertools

from httpx import AsyncClient, TimeoutException, HTTPStatusError

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Stresstests incident creation API"

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            type=str,
            help="URL for target argus host including port, ex https://argushost.no:443",
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
            help="Number of seconds to send http requests. After this no more requests will be sent but responses will be waited for",
            default=100,
        )
        parser.add_argument("-w", "--workers", type=int, help="Number of workers", default=1)

    def get_incident_data(self):
        return {
            "start_time": datetime.now().isoformat(),
            "description": "Stresstest",
            "tags": [],
        }

    async def post_incidents_until_end_time(self, url, end_time, token, client):
        created_ids = []
        incident_data = self.get_incident_data()
        while True:
            if datetime.now() >= end_time:
                break
            try:
                response = await client.post(url, json=incident_data, headers={"Authorization": f"Token {token}"})
                response.raise_for_status()
                incident = response.json()
                created_ids.append(incident["pk"])
            except TimeoutException:
                raise TimeoutException(f"Timeout waiting for POST response to {url}")
            except HTTPStatusError as e:
                msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
                raise HTTPStatusError(msg, request=e.request, response=e.response)
        return created_ids

    async def run_workers(self, url, end_time, token, worker_count):
        async with AsyncClient() as client:
            return await asyncio.gather(
                *(self.post_incidents_until_end_time(url, end_time, token, client) for _ in range(worker_count))
            )

    def handle(self, *args, **options):
        test_duration = options.get("seconds")
        url = urljoin(options.get("url"), "/api/v1/incidents/")
        token = options.get("token")
        worker_count = options.get("workers")
        loop = asyncio.get_event_loop()
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=test_duration)
        self.stdout.write("Running stresstest ...")
        try:
            result = loop.run_until_complete(self.run_workers(url, end_time, token, worker_count))
        except (TimeoutException, HTTPStatusError) as e:
            self.stderr.write(self.style.ERROR(e))
        else:
            incident_ids = list(itertools.chain.from_iterable(result))
            self.stdout.write(
                self.style.SUCCESS(
                    f"Completed in {datetime.now() - start_time} after sending {len(incident_ids)} requests."
                )
            )
