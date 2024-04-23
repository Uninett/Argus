from datetime import datetime, timedelta
from urllib.parse import urljoin
import asyncio
import itertools
from typing import Any, Dict, AnyStr, List, Tuple

from httpx import AsyncClient, TimeoutException, HTTPStatusError, post


class DatabaseMismatchError(Exception):
    pass


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

    def run(self, seconds: int) -> Tuple[List[int], timedelta]:
        """Runs a stresstest against the configured URL.
        The test will continually send requests for `seconds` seconds and stop when all requests have gotten a response.
        Returns a list containing the IDs of all created incidents and a timedelta detailing how long the test ran for.
        Since the stresstest waits for responses to all requests, the total runtime should exceed `seconds` to varying degrees.
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=seconds)
        incident_ids = self._loop.run_until_complete(self._run_stresstest_workers(end_time))
        runtime = datetime.now() - start_time
        return incident_ids, runtime

    async def _run_stresstest_workers(self, end_time: datetime) -> List[int]:
        async with AsyncClient(timeout=self.timeout) as client:
            results = await asyncio.gather(*(self._post_incidents(end_time, client) for _ in range(self.worker_count)))
            return list(itertools.chain.from_iterable(results))

    async def _post_incidents(self, end_time: datetime, client: AsyncClient) -> List[int]:
        created_ids = []
        incident_data = self._get_incident_data()
        url = self._get_incidents_v1_url()
        headers = self._get_auth_header()
        while datetime.now() < end_time:
            try:
                response = await client.post(url, json=incident_data, headers=headers)
                response.raise_for_status()
                incident = response.json()
                created_ids.append(incident["pk"])
            except TimeoutException:
                raise TimeoutException(f"Timeout waiting for POST response to {self.url}")
            except HTTPStatusError as e:
                msg = f"HTTP Error {e.response.status_code}: {e.response.content.decode('utf-8')}"
                raise HTTPStatusError(msg, request=e.request, response=e.response)
        return created_ids

    def verify(self, incident_ids: List[int]):
        """Verifies that the incidents included in `incident_ids` exist and contain the expected values"""
        self._loop.run_until_complete(self._run_verification_workers(incident_ids))

    async def _run_verification_workers(self, incident_ids: List[int]):
        ids = incident_ids.copy()
        async with AsyncClient(timeout=self.timeout) as client:
            await asyncio.gather(*(self._verify_created_incidents(ids, client) for _ in range(self.worker_count)))

    async def _verify_created_incidents(self, incident_ids: List[int], client: AsyncClient):
        while incident_ids:
            incident_id = incident_ids.pop()
            await self._verify_incident(incident_id, client)

    async def _verify_incident(self, incident_id: int, client: AsyncClient):
        expected_data = self._get_incident_data()
        id_url = urljoin(self._get_incidents_v1_url(), str(incident_id) + "/")
        try:
            response = await client.get(id_url, headers=self._get_auth_header())
            response.raise_for_status()
        except TimeoutException:
            raise TimeoutException(f"Timeout waiting for GET response to {id_url}")
        except HTTPStatusError as e:
            msg = f"HTTP Error {e.response.status_code}: {e.response.content.decode('utf-8')}"
            raise HTTPStatusError(msg, request=e.request, response=e.response)
        response_data = response.json()
        self._verify_tags(response_data, expected_data)
        self._verify_description(response_data, expected_data)

    def _verify_tags(self, response_data: Dict[str, Any], expected_data: Dict[str, Any]):
        expected_tags = set([tag["tag"] for tag in expected_data["tags"]])
        response_tags = set([tag["tag"] for tag in response_data["tags"]])
        if expected_tags != response_tags:
            msg = f'Actual tag(s) "{response_tags}" differ(s) from expected tag(s) "{expected_tags}"'
            raise DatabaseMismatchError(msg)

    def _verify_description(self, response_data: Dict[str, Any], expected_data: Dict[str, Any]):
        expected_descr = expected_data["description"]
        response_descr = response_data["description"]
        if response_descr != expected_descr:
            msg = f'Actual description "{response_descr}" differs from expected description "{expected_descr}"'
            raise DatabaseMismatchError(msg)

    def bulk_ack(self, incident_ids: List[int]):
        """Sends a request to ACK all incidents included in `incident_ids`"""
        request_data = {
            "ids": incident_ids,
            "ack": {
                "timestamp": datetime.now().isoformat(),
                "description": "Stresstest",
            },
        }
        url = urljoin(self._get_incidents_v2_url(), "acks/bulk/")
        try:
            response = post(url, json=request_data, headers=self._get_auth_header())
            response.raise_for_status()
        except TimeoutException:
            raise TimeoutException(f"Timeout waiting for POST response to {url}")
        except HTTPStatusError as e:
            msg = f"HTTP Error {e.response.status_code}: {e.response.content.decode('utf-8')}"
            raise HTTPStatusError(msg, request=e.request, response=e.response)
