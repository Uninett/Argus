from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from argus.auth.factories import AdminUserFactory
from argus.filter.factories import FilterFactory
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.plannedmaintenance.serializers import RequestPlannedMaintenanceTaskSerializer
from argus.util.datetime_utils import LOCAL_INFINITY


@tag("integration")
class PlannedMaintenanceTaskSerializerTests(TestCase):
    def setUp(self):
        self.user = AdminUserFactory()

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
        self.request_factory = APIRequestFactory()

    def test_given_correct_input_then_planned_maintenance_serializer_is_valid(self):
        request = self.request_factory.post("/")
        request.user = self.user
        now = timezone.now()
        data = {
            "start_time": now,
            "end_time": now + timedelta(hours=5),
            "description": "ABC",
            "filters": [self.open_filter.pk],
        }
        serializer = RequestPlannedMaintenanceTaskSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_given_minimal_input_then_planned_maintenance_serializer_is_valid(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "start_time": timezone.now(),
            "filters": [self.open_filter.pk],
        }
        serializer = RequestPlannedMaintenanceTaskSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_given_end_time_none_then_set_end_time_to_infinity(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "start_time": timezone.now(),
            "end_time": None,
            "description": "ABC",
            "filters": [self.open_filter.pk],
        }
        serializer = RequestPlannedMaintenanceTaskSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["end_time"], LOCAL_INFINITY)

    def test_given_valid_input_then_create_task(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "start_time": timezone.now(),
            "end_time": LOCAL_INFINITY,
            "description": "abc",
            "filters": [self.open_filter.pk],
            "created_by": self.user,
        }
        serializer = RequestPlannedMaintenanceTaskSerializer(
            context={"request": request},
        )
        obj = serializer.create(validated_data)
        self.assertEqual(obj.description, "abc")

    def test_given_valid_input_then_update_task(self):
        task = PlannedMaintenanceFactory(description="ABC", created_by=self.user)
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {"description": "new description"}
        serializer = RequestPlannedMaintenanceTaskSerializer(
            context={"request": request},
        )
        obj = serializer.update(task, validated_data)
        self.assertEqual(obj.description, "new description")
