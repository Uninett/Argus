from collections import OrderedDict
import datetime

from django.db import IntegrityError
from django.test import tag, TestCase

from rest_framework.test import APIRequestFactory

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import TimeslotFactory
from argus.notificationprofile.models import Timeslot
from argus.notificationprofile.serializers import TimeslotSerializer


@tag("integration")
class TimeslotSerializerTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        # When creating a User which is a person, we also create a default Timeslot
        self.default_timeslot = Timeslot.objects.get(user=self.user)
        self.request_factory = APIRequestFactory()

    def test_timeslot_serializer_is_valid_with_correct_input(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "name": "vfrgthj",
            "time_recurrences": [
                {
                    "days": [1, 2, 3, 4, 5],
                    "start": "00:00:00",
                    "end": "16:00:00",
                }
            ],
        }
        serializer = TimeslotSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_timeslot_serializer_is_invalid_with_duplicate_name(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "name": self.default_timeslot.name,
            "time_recurrences": [
                {
                    "days": [1, 2, 3, 4, 5],
                    "start": "00:00:00",
                    "end": "16:00:00",
                }
            ],
        }
        serializer = TimeslotSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_can_create_timeslot(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "name": "vfrgthj",
            "time_recurrences": [
                OrderedDict([("days", {1, 2, 3, 4, 5}), ("start", datetime.time(8, 0)), ("end", datetime.time(16, 0))])
            ],
            "user": self.user,
        }
        serializer = TimeslotSerializer(
            context={"request": request},
        )
        obj = serializer.create(validated_data)
        self.assertEqual(obj.name, "vfrgthj")

    def test_cannot_create_timeslot_with_duplicate_name(self):
        request = self.request_factory.post("/")
        request.user = self.user
        # Reuse the name of the default timeslot
        validated_data = {
            "name": self.default_timeslot.name,
            "time_recurrences": [
                OrderedDict([("days", {1, 2, 3, 4, 5}), ("start", datetime.time(8, 0)), ("end", datetime.time(16, 0))])
            ],
            "user": self.user,
        }
        serializer = TimeslotSerializer(
            context={"request": request},
        )
        # serializer.create works on already validated data
        with self.assertRaises(IntegrityError):
            serializer.create(validated_data)

    def test_can_update_timeslot(self):
        timeslot = TimeslotFactory(name="existing name", user=self.user)
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "name": "new name",
            "time_recurrences": [
                OrderedDict([("days", {1, 2, 3, 4, 5}), ("start", datetime.time(8, 0)), ("end", datetime.time(16, 0))])
            ],
            "user": self.user,
        }
        serializer = TimeslotSerializer(
            context={"request": request},
        )
        obj = serializer.update(timeslot, validated_data)
        self.assertEqual(obj.name, "new name")

    def test_cannot_update_timeslot_with_duplicate_name(self):
        timeslot = TimeslotFactory(name="existing name", user=self.user)
        request = self.request_factory.post("/")
        request.user = self.user
        # Reuse the name of the default timeslot
        validated_data = {
            "name": self.default_timeslot.name,
            "time_recurrences": [
                OrderedDict([("days", {1, 2, 3, 4, 5}), ("start", datetime.time(8, 0)), ("end", datetime.time(16, 0))])
            ],
            "user": self.user,
        }
        serializer = TimeslotSerializer(
            context={"request": request},
        )
        # serializer.create works on already validated data
        with self.assertRaises(IntegrityError):
            serializer.update(timeslot, validated_data)
