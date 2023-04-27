from datetime import datetime, timedelta
from urllib.parse import urljoin
import asyncio
import itertools

from httpx import AsyncClient, TimeoutException, HTTPStatusError

from django.core.management.base import BaseCommand


class DatabaseMismatchError(Exception):
    pass


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

    async def verify_created_incidents(self, url, token, incident_ids, client):
        expected_data = self.get_incident_data()
        while incident_ids:
            id = incident_ids.pop()
            id_url = urljoin(url, str(id) + "/")
            try:
                response = await client.get(id_url, headers={"Authorization": f"Token {token}"})
                response.raise_for_status()
            except TimeoutException:
                raise TimeoutException(f"Timeout waiting for GET response to {id_url}")
            except HTTPStatusError as e:
                msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
                raise HTTPStatusError(msg, request=e.request, response=e.response)
            response_data = response.json()
            self.verify_tags(response_data, expected_data)
            self.verify_description(response_data, expected_data)

    def verify_tags(self, response_data, expected_data):
        expected_tags = set([tag["tag"] for tag in expected_data["tags"]])
        response_tags = set([tag["tag"] for tag in response_data["tags"]])
        if expected_tags != response_tags:
            msg = f'Actual tag(s) "{response_tags}" differ from expected tag(s) "{expected_tags}"'
            raise DatabaseMismatchError(msg)

    def verify_description(self, response_data, expected_data):
        expected_descr = expected_data["description"]
        response_descr = response_data["description"]
        if response_descr != expected_descr:
            msg = f'Actual description "{response_descr}" differ from expected description "{expected_descr}"'
            raise DatabaseMismatchError(msg)

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
