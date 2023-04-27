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
        parser.add_argument("-t", "--timeout", type=int, help="Timeout for requests", default=5)
        parser.add_argument("-w", "--workers", type=int, help="Number of workers", default=1)

    def handle(self, *args, **options):
        url = urljoin(options.get("url"), "/api/v1/incidents/")
        tester = StressTester(url, options.get("token"), options.get("timeout"), options.get("workers"))
        loop = asyncio.get_event_loop()
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=options.get("seconds"))
        self.stdout.write("Running stresstest ...")
        try:
            incident_ids = loop.run_until_complete(tester.run_stresstest_workers(end_time))
        except (TimeoutException, HTTPStatusError) as e:
            self.stderr.write(self.style.ERROR(e))
            return
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed in {datetime.now() - start_time} after sending {len(incident_ids)} requests."
            )
        )
        self.stdout.write("Verifying incidents were created correctly ...")
        try:
            loop.run_until_complete(tester.run_verification_workers(incident_ids))
        except (DatabaseMismatchError, HTTPStatusError, TimeoutException) as e:
            self.stderr.write(self.style.ERROR(e))
            return
        self.stdout.write(self.style.SUCCESS("Verification complete with no errors."))


class StressTester:
    def __init__(self, url, token, timeout, worker_count):
        self.url = url
        self.token = token
        self.timeout = timeout
        self.worker_count = worker_count

    def _get_incident_data(self):
        return {
            "start_time": datetime.now().isoformat(),
            "description": "Stresstest",
            "tags": [{"tag": "problem_type=stresstest"}],
        }

    async def _post_incidents_until_end_time(self, end_time, client):
        created_ids = []
        incident_data = self._get_incident_data()
        while datetime.now() < end_time:
            try:
                response = await client.post(
                    self.url, json=incident_data, headers={"Authorization": f"Token {self.token}"}
                )
                response.raise_for_status()
                incident = response.json()
                created_ids.append(incident["pk"])
            except TimeoutException:
                raise TimeoutException(f"Timeout waiting for POST response to {self.url}")
            except HTTPStatusError as e:
                msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
                raise HTTPStatusError(msg, request=e.request, response=e.response)
        return created_ids

    async def run_stresstest_workers(self, end_time):
        async with AsyncClient(timeout=self.timeout) as client:
            results = await asyncio.gather(
                *(self._post_incidents_until_end_time(end_time, client) for _ in range(self.worker_count))
            )
            return list(itertools.chain.from_iterable(results))

    async def run_verification_workers(self, incident_ids):
        async with AsyncClient(timeout=self.timeout) as client:
            await asyncio.gather(
                *(self._verify_created_incidents(incident_ids, client) for _ in range(self.worker_count))
            )

    async def _verify_created_incidents(self, incident_ids, client):
        expected_data = self._get_incident_data()
        while incident_ids:
            id = incident_ids.pop()
            id_url = urljoin(self.url, str(id) + "/")
            try:
                response = await client.get(id_url, headers={"Authorization": f"Token {self.token}"})
                response.raise_for_status()
            except TimeoutException:
                raise TimeoutException(f"Timeout waiting for GET response to {id_url}")
            except HTTPStatusError as e:
                msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
                raise HTTPStatusError(msg, request=e.request, response=e.response)
            response_data = response.json()
            self._verify_tags(response_data, expected_data)
            self._verify_description(response_data, expected_data)

    def _verify_tags(self, response_data, expected_data):
        expected_tags = set([tag["tag"] for tag in expected_data["tags"]])
        response_tags = set([tag["tag"] for tag in response_data["tags"]])
        if expected_tags != response_tags:
            msg = f'Actual tag(s) "{response_tags}" differ from expected tag(s) "{expected_tags}"'
            raise DatabaseMismatchError(msg)

    def _verify_description(self, response_data, expected_data):
        expected_descr = expected_data["description"]
        response_descr = response_data["description"]
        if response_descr != expected_descr:
            msg = f'Actual description "{response_descr}" differ from expected description "{expected_descr}"'
            raise DatabaseMismatchError(msg)
