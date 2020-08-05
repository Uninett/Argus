from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import is_aware, make_aware

from argus.auth.models import User
from argus.site.utils import duplicate
from ..models import Incident, Object, ObjectType, ProblemType, SourceSystem, SourceSystemType


class EndTimeInfinityFieldTests(TestCase):
    def setUp(self):
        source_system_type = SourceSystemType.objects.create(name="Type")
        source_system_user = User.objects.create_user(username="system_1")
        source_system1 = SourceSystem.objects.create(name="System 1", type=source_system_type, user=source_system_user)
        object_type = ObjectType.objects.create(name="ObjectType")
        object1 = Object.objects.create(name="Object 1", object_id="123", type=object_type)
        problem_type = ProblemType.objects.create(name="ProblemType")

        self.incident1 = Incident.objects.create(
            start_time=make_aware(datetime(2000, 1, 1)),
            source=source_system1,
            source_incident_id="1",
            object=object1,
            problem_type=problem_type,
        )
        self.incident2 = duplicate(self.incident1, source_incident_id="2")
        self.incident3 = duplicate(self.incident1, source_incident_id="3")

    @staticmethod
    def _save_end_time(incident: Incident, end_time):
        incident.end_time = end_time
        incident.save(update_fields=["end_time"])

    def _assert_inserting_infinity_end_time_retrieves(self, insert_value, retrieval_value):
        self._save_end_time(self.incident1, insert_value)
        self.assertTrue(is_aware(self.incident1.end_time))
        self.assertEqual(self.incident1.end_time.replace(tzinfo=None), retrieval_value)

    def test_inserting_infinity_values_retrieves_infinity_values(self):
        self._assert_inserting_infinity_end_time_retrieves(datetime.max, datetime.max)
        self._assert_inserting_infinity_end_time_retrieves(datetime.min, datetime.min)
        self._assert_inserting_infinity_end_time_retrieves(
            datetime.max.replace(tzinfo=timezone.get_default_timezone()), datetime.max
        )
        self._assert_inserting_infinity_end_time_retrieves(
            datetime.min.replace(tzinfo=timezone.get_default_timezone()), datetime.min
        )
        self._assert_inserting_infinity_end_time_retrieves("infinity", datetime.max)
        self._assert_inserting_infinity_end_time_retrieves("-infinity", datetime.min)

    def test_inserting_illegal_values_fails(self):
        self.incident1.end_time = "illegal"
        with self.assertRaises(ValidationError):
            self.incident1.save()

    def _assert_inserting_standard_datetime_end_time_retrieves_the_same(self, insert_value):
        insert_value = make_aware(insert_value)
        self._save_end_time(self.incident1, insert_value)
        if insert_value is not None:
            self.assertTrue(is_aware(self.incident1.end_time))
        self.assertEqual(self.incident1.end_time, insert_value)

    def test_inserting_standard_values_retrieves_the_same(self):
        self._save_end_time(self.incident1, None)
        self.assertEqual(self.incident1.end_time, None)

        self._assert_inserting_standard_datetime_end_time_retrieves_the_same(datetime(2000, 1, 1))
        self._assert_inserting_standard_datetime_end_time_retrieves_the_same(datetime.now())
        self._assert_inserting_standard_datetime_end_time_retrieves_the_same(datetime.max - timedelta(days=1))
        self._assert_inserting_standard_datetime_end_time_retrieves_the_same(datetime.min + timedelta(days=1))

    def test_sorting_by_end_time_sorts_expectedly(self):
        self._save_end_time(self.incident1, make_aware(datetime(2000, 1, 1)))
        self._save_end_time(self.incident2, make_aware(datetime(1999, 12, 31)))
        self._save_end_time(self.incident3, make_aware(datetime(2000, 1, 2)))
        self.assertListEqual(
            list(Incident.objects.order_by("end_time")), [self.incident2, self.incident1, self.incident3]
        )

        self._save_end_time(self.incident1, "-infinity")
        self._save_end_time(self.incident2, make_aware(datetime(2000, 1, 1)))
        self._save_end_time(self.incident3, "infinity")
        self.assertListEqual(
            list(Incident.objects.order_by("end_time")), [self.incident1, self.incident2, self.incident3]
        )

    def test_filtering_on_end_time_filters_expectedly(self):
        end_time2 = make_aware(datetime(2000, 1, 1))
        self._save_end_time(self.incident1, "-infinity")
        self._save_end_time(self.incident2, end_time2)
        self._save_end_time(self.incident3, "infinity")
        self.assertListEqual(
            list(Incident.objects.filter(end_time__gte=end_time2).order_by("end_time")),
            [self.incident2, self.incident3],
        )
        self.assertListEqual(
            list(Incident.objects.filter(end_time__lte=end_time2).order_by("end_time")),
            [self.incident1, self.incident2],
        )

        self.assertListEqual(
            list(Incident.objects.filter(end_time__gte="-infinity").order_by("end_time")),
            [self.incident1, self.incident2, self.incident3],
        )
        self.assertListEqual(
            list(Incident.objects.filter(end_time__lte="infinity").order_by("end_time")),
            [self.incident1, self.incident2, self.incident3],
        )

        self.assertFalse(Incident.objects.filter(end_time__lt="-infinity").exists())
        self.assertFalse(Incident.objects.filter(end_time__gt="infinity").exists())
