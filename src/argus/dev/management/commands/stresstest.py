from datetime import datetime, timedelta
from urllib.parse import urljoin
import asyncio
import itertools
from typing import Any, Dict, AnyStr, List

import httpx
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
            help="Number of seconds to send http requests. After this no more requests will be sent but responses will be waited for. Default 10s",
            default=10,
        )
        parser.add_argument("-t", "--timeout", type=int, help="Timeout for requests. Default 5s", default=5)
        parser.add_argument("-w", "--workers", type=int, help="Number of workers. Default 1", default=1)
        parser.add_argument("-b", "--bulk", action="store_true", help="Bulk ACK created incidents")

    def handle(self, *args, **options):
        tester = StressTester(options.get("url"), options.get("token"), options.get("timeout"), options.get("workers"))
        try:
            incident_ids = self._run_stresstest(tester, options.get("seconds"))
            self._verify_incidents(tester, incident_ids)
            if options.get("bulk"):
                self._bulk_ack_incidents(tester, incident_ids)
        except (DatabaseMismatchError, HTTPStatusError, TimeoutException) as e:
            self.stderr.write(self.style.ERROR(e))

    def _run_stresstest(self, tester: "StressTester", seconds: int) -> List[int]:
        self.stdout.write("Running stresstest ...")
        incident_ids, runtime = tester.run(seconds)
        requests_per_second = len(incident_ids) / runtime.seconds
        self.stdout.write(
            self.style.SUCCESS(f"Completed in {runtime} with an average of {requests_per_second} requests per second")
        )
        return incident_ids

    def _verify_incidents(self, tester: "StressTester", incident_ids: List[int]):
        self.stdout.write("Verifying incidents were created correctly ...")
        tester.verify(incident_ids)
        self.stdout.write(self.style.SUCCESS("Verification complete with no errors."))

    def _bulk_ack_incidents(self, tester: "StressTester", incident_ids: List[int]):
        self.stdout.write("Bulk ACKing incidents ...")
        tester.bulk_ack(incident_ids)
        self.stdout.write(self.style.SUCCESS("Succesfully bulk ACK'd"))


class StressTester:
    def __init__(self, url: str, token: str, timeout: int, worker_count: int):
        self.url = url
        self.token = token
        self.timeout = timeout
        self.worker_count = worker_count
        self._loop = asyncio.get_event_loop()

    def _get_incident_data(self) -> Dict[str, Any]:
        return {
            "start_time": datetime.now().isoformat(),
            "description": "Stresstest",
            "tags": [{"tag": "problem_type=stresstest"}],
        }

    def _get_auth_header(self) -> Dict[str, str]:
        return {"Authorization": f"Token {self.token}"}

    def _get_incidents_v1_url(self) -> AnyStr:
        return urljoin(self.url, "/api/v1/incidents/")

    def _get_incidents_v2_url(self) -> AnyStr:
        return urljoin(self.url, "/api/v2/incidents/")

    async def _post_incidents(self, end_time: datetime, client: AsyncClient) -> List[int]:
        created_ids = []
        incident_data = self._get_incident_data()
        while datetime.now() < end_time:
            try:
                response = await client.post(
                    self._get_incidents_v1_url(), json=incident_data, headers=self._get_auth_header()
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

    def run(self, seconds: int) -> tuple(List[int], timedelta):
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=seconds)
        incident_ids = self._loop.run_until_complete(self._run_stresstest_workers(end_time))
        runtime = datetime.now() - start_time
        return incident_ids, runtime

    async def _run_stresstest_workers(self, end_time: datetime) -> List[int]:
        async with AsyncClient(timeout=self.timeout) as client:
            results = await asyncio.gather(*(self._post_incidents(end_time, client) for _ in range(self.worker_count)))
            return list(itertools.chain.from_iterable(results))

    def verify(self, incident_ids: List[int]):
        self._loop.run_until_complete(self._run_verification_workers(incident_ids))

    async def _run_verification_workers(self, incident_ids: List[int]):
        ids = incident_ids.copy()
        async with AsyncClient(timeout=self.timeout) as client:
            await asyncio.gather(*(self._verify_created_incidents(ids, client) for _ in range(self.worker_count)))

    async def _verify_created_incidents(self, incident_ids: List[int], client: AsyncClient):
        while incident_ids:
            incident_id = incident_ids.pop()
            self._verify_incident(incident_id, client)

    async def _verify_incident(self, incident_id: int, client: AsyncClient):
        expected_data = self._get_incident_data()
        id_url = urljoin(self._get_incidents_v1_url(), str(incident_id) + "/")
        try:
            response = await client.get(id_url, headers=self._get_auth_header())
            response.raise_for_status()
        except TimeoutException:
            raise TimeoutException(f"Timeout waiting for GET response to {id_url}")
        except HTTPStatusError as e:
            msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
            raise HTTPStatusError(msg, request=e.request, response=e.response)
        response_data = response.json()
        self._verify_tags(response_data, expected_data)
        self._verify_description(response_data, expected_data)

    def _verify_tags(self, response_data: Dict[str, Any], expected_data: Dict[str, Any]):
        expected_tags = set([tag["tag"] for tag in expected_data["tags"]])
        response_tags = set([tag["tag"] for tag in response_data["tags"]])
        if expected_tags != response_tags:
            msg = f'Actual tag(s) "{response_tags}" differ from expected tag(s) "{expected_tags}"'
            raise DatabaseMismatchError(msg)

    def _verify_description(self, response_data: Dict[str, Any], expected_data: Dict[str, Any]):
        expected_descr = expected_data["description"]
        response_descr = response_data["description"]
        if response_descr != expected_descr:
            msg = f'Actual description "{response_descr}" differ from expected description "{expected_descr}"'
            raise DatabaseMismatchError(msg)

    def bulk_ack(self, incident_ids: List[int]):
        request_data = {
            "ids": incident_ids,
            "ack": {
                "timestamp": datetime.now().isoformat(),
                "description": "Stresstest",
            },
        }
        url = urljoin(self._get_incidents_v2_url(), "acks/bulk/")
        try:
            response = httpx.post(url, json=request_data, headers=self._get_auth_header())
            response.raise_for_status()
        except TimeoutException:
            raise TimeoutException(f"Timeout waiting for POST response to {url}")
        except HTTPStatusError as e:
            msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
            raise HTTPStatusError(msg, request=e.request, response=e.response)
