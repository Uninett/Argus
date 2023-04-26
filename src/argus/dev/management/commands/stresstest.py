from datetime import datetime, timedelta
from urllib.parse import urljoin
import asyncio
import itertools
import requests

from httpx import HTTPError, AsyncClient

from django.core.management.base import BaseCommand


class DatabaseMismatchError(Exception):
    pass


class Command(BaseCommand):
    help = "Stresstests incident creation API"

    def add_arguments(self, parser):
        parser.add_argument(
            "-s",
            "--seconds",
            type=int,
            help="Number of seconds to send http requests. After this no more requests will be sent but responses will be waited for",
            default=100,
        )
        parser.add_argument(
            "-u",
            "--url",
            type=str,
            help="URL for target argus host including port, ex https://argushost.no:443",
            required=True,
        )
        parser.add_argument(
            "-t",
            "--token",
            type=str,
            help="Token for authenticating against target API. The token must belong to a user that is associated with a source system",
            required=True,
        )
        parser.add_argument("-n", type=int, help="Number of workers", default=1)

    def get_incident_data(self):
        return {
            "start_time": datetime.now().isoformat(),
            "description": "Stresstest",
            "tags": [{"tag": "problem_type=stresstest"}],
        }

    async def post_incidents_until_end_time(self, url, end_time, token, client):
        request_counter = 0
        incident_data = self.get_incident_data()
        created_ids = []
        while True:
            if datetime.now() >= end_time:
                break
            # Can raise HTTPError but does not need to be handled here
            response = await client.post(url, json=incident_data, headers={"Authorization": f"Token {token}"})
            try:
                response.raise_for_status()
                incident = response.json()
                created_ids.append(incident["pk"])
            except HTTPError:
                msg = f"HTTP error {response.status_code}: {response.content.decode('utf-8')}"
                raise HTTPError(msg)
            request_counter += 1
        return created_ids

    async def run_workers(self, url, end_time, token, worker_count):
        async with AsyncClient() as client:
            return await asyncio.gather(
                *(self.post_incidents_until_end_time(url, end_time, token, client) for _ in range(worker_count))
            )

    def verify_created_incidents(self, incident_ids, url, token):
        expected_data = self.get_incident_data()
        for id in incident_ids:
            id_url = urljoin(url, str(id))
            response = requests.get(id_url, headers={"Authorization": f"Token {token}"})
            response_data = response.json()
            self.verify_tags(response_data, expected_data)
            self.verify_description(response_data, expected_data)

    def verify_tags(self, response_data, expected_data):
        expected_tags = set([tag["tag"] for tag in expected_data["tags"]])
        response_data = set([tag["tag"] for tag in response_data["tags"]])
        if expected_tags != response_data:
            raise DatabaseMismatchError("Expected tags are different from actual tags")

    def verify_description(self, response_data, expected_data):
        if response_data["description"] != expected_data["description"]:
            raise DatabaseMismatchError("Expected description is different from actual description")

    def handle(self, *args, **options):
        test_duration = options.get("seconds")
        url = urljoin(options.get("url"), "/api/v1/incidents/")
        token = options.get("token")
        worker_count = options.get("n")
        loop = asyncio.get_event_loop()
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=test_duration)
        self.stdout.write("Starting stresstest ...")
        try:
            result = loop.run_until_complete(self.run_workers(url, end_time, token, worker_count))
        except HTTPError as e:
            self.stderr.write(self.style.ERROR(e))
            return
        all_created_ids = list(itertools.chain.from_iterable(result))
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed in {datetime.now() - start_time} after sending {len(all_created_ids)} requests."
            )
        )
        self.stdout.write("Verifying incidents were created correctly ...")
        try:
            self.verify_created_incidents(all_created_ids, url, token)
        except DatabaseMismatchError as e:
            self.stderr.write(self.style.ERROR(e))
            return
        self.stdout.write(self.style.SUCCESS("Verification complete with no errors."))
