from datetime import datetime, timedelta
from urllib.parse import urljoin
import asyncio
import itertools

from httpx import HTTPError, AsyncClient, ReadTimeout

from django.core.management.base import BaseCommand


class DatabaseMismatchError(Exception):
    pass


class Command(BaseCommand):
    help = "Stresstests incident creation API"
    DEFAULT_TIMEOUT = 5

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

    async def post_incidents_until_end_time(self, url, end_time, token, client, timeout=DEFAULT_TIMEOUT):
        request_counter = 0
        incident_data = self.get_incident_data()
        created_ids = []
        while True:
            if datetime.now() >= end_time:
                break
            try:
                response = await client.post(
                    url, json=incident_data, headers={"Authorization": f"Token {token}"}, timeout=timeout
                )
            except ReadTimeout:
                raise HTTPError(f"Timeout ({timeout}s) waiting for POST response to {url}")
            try:
                response.raise_for_status()
                incident = response.json()
                created_ids.append(incident["pk"])
            except HTTPError:
                msg = f"HTTP error {response.status_code}: {response.content.decode('utf-8')}"
                raise HTTPError(msg)
            request_counter += 1
        return created_ids

    async def run_stresstest_workers(self, url, end_time, token, worker_count):
        async with AsyncClient() as client:
            return await asyncio.gather(
                *(self.post_incidents_until_end_time(url, end_time, token, client) for _ in range(worker_count))
            )

    async def run_verification_workers(self, url, token, incident_ids, worker_count):
        async with AsyncClient() as client:
            return await asyncio.gather(
                *(self.verify_created_incidents(url, token, incident_ids, client) for _ in range(worker_count))
            )

    async def verify_created_incidents(self, url, token, incident_ids, client, timeout=DEFAULT_TIMEOUT):
        expected_data = self.get_incident_data()
        while incident_ids:
            id = incident_ids.pop()
            id_url = urljoin(url, str(id) + "/")
            try:
                response = await client.get(id_url, headers={"Authorization": f"Token {token}"}, timeout=timeout)
            except ReadTimeout:
                raise HTTPError(f"Timeout ({timeout}s) waiting for GET response to {id_url}")
            try:
                response.raise_for_status()
            except HTTPError:
                msg = f"HTTP error {response.status_code}: {response.content.decode('utf-8')}"
                raise HTTPError(msg)
            response_data = response.json()
            self.verify_tags(response_data, expected_data)
            self.verify_description(response_data, expected_data)

    def verify_tags(self, response_data, expected_data):
        expected_tags = set([tag["tag"] for tag in expected_data["tags"]])
        response_tags = set([tag["tag"] for tag in response_data["tags"]])
        if expected_tags != response_tags:
            msg = f'Actual tags "{response_tags}" differ from expected tags "{expected_tags}"'
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
        worker_count = options.get("n")
        loop = asyncio.get_event_loop()
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=test_duration)
        self.stdout.write("Starting stresstest ...")
        try:
            result = loop.run_until_complete(self.run_stresstest_workers(url, end_time, token, worker_count))
        except HTTPError as e:
            self.stderr.write(self.style.ERROR(e))
            return
        incident_ids = list(itertools.chain.from_iterable(result))
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed in {datetime.now() - start_time} after sending {len(incident_ids)} requests."
            )
        )
        self.stdout.write("Verifying incidents were created correctly ...")
        try:
            loop.run_until_complete(self.run_verification_workers(url, token, incident_ids, worker_count))
        except (DatabaseMismatchError, HTTPError) as e:
            self.stderr.write(self.style.ERROR(e))
            return
        self.stdout.write(self.style.SUCCESS("Verification complete with no errors."))
