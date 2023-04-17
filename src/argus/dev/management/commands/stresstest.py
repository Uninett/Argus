from datetime import datetime
from urllib.parse import urljoin
import asyncio

import httpx
from httpx import HTTPError

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Stresstests incident creation API"

    INCIDENT_DATA = {
        "source": "1",
        "start_time": "2023-04-18T15:44:00+02:00",
        "description": "Stresstest",
        "tags": [],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "-s", "--seconds", type=int, help="Number of seconds the stresstest should last", default=100
        )
        parser.add_argument(
            "-u",
            "--url",
            type=str,
            help="URL for target argus host including port, ex https://argushost.no:443",
            required=True,
        )
        parser.add_argument(
            "-t", "--token", type=str, help="Token for authenticating against target API", required=True
        )
        parser.add_argument("-n", type=int, help="Number of parallel connections", default=1)

    async def spam_post_incident(self, url, duration, token, client):
        request_counter = 0
        stresstest_start = datetime.now()
        while True:
            # Can raise HTTPError but does not need to be handled here
            response = await client.post(url, json=self.INCIDENT_DATA, headers={"Authorization": f"Token {token}"})
            try:
                response.raise_for_status()
            except HTTPError:
                msg = f"HTTP error {response.status_code}: {response.content.decode('utf-8')}"
                raise HTTPError(msg)
            request_counter += 1
            current_duration = (datetime.now() - stresstest_start).seconds
            if current_duration >= duration:
                break
        return request_counter

    async def run_spam_workers(self, url, duration, token, worker_count):
        async with httpx.AsyncClient() as client:
            return await asyncio.gather(
                *(self.spam_post_incident(url, duration, token, client) for _ in range(worker_count))
            )

    def handle(self, *args, **options):
        test_duration = options.get("seconds")
        url = urljoin(options.get("url"), "/api/v1/incidents/")
        token = options.get("token")
        worker_count = options.get("n")
        loop = asyncio.get_event_loop()
        try:
            result = loop.run_until_complete(self.run_spam_workers(url, test_duration, token, worker_count))
        except HTTPError as e:
            self.stderr.write(self.style.ERROR(e))
        else:
            total_requests = sum(result)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Stresstest complete with no errors. {total_requests} requests were sent in {test_duration} seconds."
                )
            )
