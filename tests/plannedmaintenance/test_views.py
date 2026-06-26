from datetime import timedelta

from django.utils import timezone
from django.test import tag
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import AdminUserFactory, PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.plannedmaintenance.models import PlannedMaintenanceTask
from argus.util.datetime_utils import LOCAL_INFINITY
from argus.util.testing import connect_signals, disconnect_signals


@tag("API", "integration")
class PlannedMaintenanceTaskViewTests(APITestCase):
    ENDPOINT = "/api/v2/plannedmaintenance/"

    def setUp(self):
        disconnect_signals()
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()

        self.user_rest_client = APIClient()
        self.user_rest_client.force_authenticate(user=self.user)

        self.admin_user_rest_client = APIClient()
        self.admin_user_rest_client.force_authenticate(user=self.staff_user)

        now = timezone.now()
        self.future_pm = PlannedMaintenanceFactory(
            start_time=now + timedelta(days=1),
            end_time=LOCAL_INFINITY,
        )
        self.current_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(hours=1),
            end_time=LOCAL_INFINITY,
        )
        self.past_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=1),
        )
        self.recently_ended_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(minutes=60),
            end_time=now - timedelta(minutes=15),
        )

        self.open_filter = FilterFactory(filter={"open": True})

    def teardown(self):
        connect_signals()

    def test_when_getting_list_as_non_admin_then_return_200_ok(self):
        response = self.user_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_when_getting_list__as_admin_then_return_200_ok(self):
        response = self.admin_user_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_when_getting_list_then_return_all_planned_maintenance_tasks(self):
        response = self.admin_user_rest_client.get(path=self.ENDPOINT)
        all_response_pks = {task["pk"] for task in response.data}
        self.assertIn(self.future_pm.pk, all_response_pks)
        self.assertIn(self.current_pm.pk, all_response_pks)
        self.assertIn(self.recently_ended_pm.pk, all_response_pks)
        self.assertIn(self.past_pm.pk, all_response_pks)

    def test_when_getting_specific_task_as_non_admin_then_return_200(self):
        pm_path = f"{self.ENDPOINT}{self.current_pm.pk}/"
        response = self.user_rest_client.get(path=pm_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_when_getting_specific_task_as_admin_then_return_200_ok(self):
        pm_path = f"{self.ENDPOINT}{self.current_pm.pk}/"
        response = self.admin_user_rest_client.get(path=pm_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_when_getting_specific_task_then_return_task(self):
        pm_path = f"{self.ENDPOINT}{self.current_pm.pk}/"
        response = self.admin_user_rest_client.get(path=pm_path)
        self.assertEqual(response.data["pk"], self.current_pm.pk)

    def test_when_posting_as_non_admin_then_return_403_forbidden(self):
        data = {
            "start_time": "2025-05-14T11:14:41.391Z",
            "end_time": "2025-05-16T11:14:41.391Z",
            "description": "ABC",
            "filters": [self.open_filter.pk],
        }
        response = self.user_rest_client.post(path=self.ENDPOINT, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(PlannedMaintenanceTask.objects.filter(description=data["description"]).exists())

    def test_given_valid_values_then_should_create_task(self):
        response = self.admin_user_rest_client.post(
            path=self.ENDPOINT,
            data={
                "start_time": "2025-05-14T11:14:41.391Z",
                "end_time": "2025-05-16T11:14:41.391Z",
                "description": "ABC",
                "filters": [self.open_filter.pk],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PlannedMaintenanceTask.objects.filter(pk=response.data["pk"]).exists())

    def test_given_no_end_time_then_set_end_time_to_infinite(self):
        response = self.admin_user_rest_client.post(
            path=self.ENDPOINT,
            data={
                "start_time": "2025-05-14T11:14:41.391Z",
                "description": "ABC",
                "filters": [self.open_filter.pk],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pm = PlannedMaintenanceTask.objects.filter(pk=response.data["pk"]).first()
        self.assertTrue(pm)
        self.assertEqual(pm.end_time, LOCAL_INFINITY)

    def test_given_end_time_none_then_set_end_time_to_infinite(self):
        response = self.admin_user_rest_client.post(
            path=self.ENDPOINT,
            data={
                "start_time": "2025-05-14T11:14:41.391Z",
                "end_time": None,
                "description": "ABC",
                "filters": [self.open_filter.pk],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pm = PlannedMaintenanceTask.objects.filter(pk=response.data["pk"]).first()
        self.assertTrue(pm)
        self.assertEqual(pm.end_time, LOCAL_INFINITY)

    def test_given_end_time_before_start_time_then_should_return_400_bad_request(self):
        data = {
            "start_time": "2025-05-14T11:14:41.391Z",
            "end_time": "2025-05-12T11:14:41.391Z",
            "description": "ABC",
            "filters": [self.open_filter.pk],
        }
        response = self.admin_user_rest_client.post(
            path=self.ENDPOINT,
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PlannedMaintenanceTask.objects.filter(description=data["description"]).exists())

    def test_when_updating_pm_as_non_admin_then_return_403_forbidden(self):
        description = "ABC"
        response = self.user_rest_client.patch(
            path=f"{self.ENDPOINT}{self.future_pm.pk}/", data={"description": description}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.future_pm.refresh_from_db()
        self.assertNotEqual(self.future_pm.description, description)

    def test_given_valid_values_when_updating_future_pm_then_change_values(self):
        response = self.admin_user_rest_client.patch(
            path=f"{self.ENDPOINT}{self.future_pm.pk}/",
            data={
                "start_time": timezone.now().isoformat(),
                "description": "ABC",
                "filters": [self.open_filter.pk],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.future_pm.refresh_from_db()
        self.assertEqual(self.future_pm.description, "ABC")

    def test_when_updating_old_pm_then_return_400_bad_request(self):
        description = "ABC"
        response = self.admin_user_rest_client.patch(
            path=f"{self.ENDPOINT}{self.past_pm.pk}/", data={"description": description}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.past_pm.refresh_from_db()
        self.assertNotEqual(self.past_pm.description, description)

    def test_when_updating_start_time_of_current_pm_then_return_400_bad_request(self):
        start_time = self.current_pm.start_time
        response = self.admin_user_rest_client.patch(
            path=f"{self.ENDPOINT}{self.current_pm.pk}/", data={"start_time": timezone.now().isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.current_pm.refresh_from_db()
        self.assertEqual(self.current_pm.start_time, start_time)

    def test_when_updating_start_time_of_recently_ended_pm_then_return_400_bad_request(self):
        start_time = self.recently_ended_pm.start_time
        response = self.admin_user_rest_client.patch(
            path=f"{self.ENDPOINT}{self.recently_ended_pm.pk}/", data={"start_time": timezone.now().isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.recently_ended_pm.refresh_from_db()
        self.assertEqual(self.recently_ended_pm.start_time, start_time)

    def test_when_deleting_future_task_as_admin_then_should_delete_task(self):
        pm_path = f"{self.ENDPOINT}{self.future_pm.pk}/"
        response = self.admin_user_rest_client.delete(path=pm_path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PlannedMaintenanceTask.objects.filter(pk=self.future_pm.pk).exists())

    def test_when_deleting_current_task_then_should_return_400_bad_request(self):
        pm_path = f"{self.ENDPOINT}{self.current_pm.pk}/"
        response = self.admin_user_rest_client.delete(path=pm_path)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PlannedMaintenanceTask.objects.filter(pk=self.future_pm.pk).exists())

    def test_when_deleting_past_task_then_should_return_400_bad_request(self):
        pm_path = f"{self.ENDPOINT}{self.past_pm.pk}/"
        response = self.admin_user_rest_client.delete(path=pm_path)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PlannedMaintenanceTask.objects.filter(pk=self.future_pm.pk).exists())

    def test_when_deleting_task_as_non_admin_then_should_return_403_forbidden(self):
        pm_path = f"{self.ENDPOINT}{self.future_pm.pk}/"
        response = self.user_rest_client.delete(path=pm_path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(PlannedMaintenanceTask.objects.filter(pk=self.future_pm.pk).exists())
