from collections import OrderedDict
import datetime

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIRequestFactory
from rest_framework import serializers

from argus.auth.factories import PersonUserFactory
from argus.incident.factories import IncidentFactory
from argus.incident.serializers import AcknowledgementSerializer
from argus.incident.serializers import UpdateAcknowledgementSerializer
from argus.util.testing import disconnect_signals, connect_signals


class AcknowledgementSerializerTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.user = PersonUserFactory()
        self.request_factory = APIRequestFactory()

    def tearDown(self):
        connect_signals()

    def test_create_golden_path(self):
        request = self.request_factory.post("/")
        request.user = self.user
        incident = IncidentFactory()
        timestamp = timezone.now()
        data = {
            "event": {
                "actor": {},  # Forced to request.user
                "timestamp": timestamp.isoformat(),
                "type": "STA",  # Forced to ACK
                "description": "string",
            },
            "expiration": None,
        }
        serializer = AcknowledgementSerializer(data=data, context={"request": request})
        serializer.is_valid()
        validated_data = serializer.validated_data
        validated_data["actor"] = self.user
        validated_data["incident"] = incident
        ack = serializer.create(validated_data)
        self.assertEqual(ack.event.incident, incident)
        self.assertEqual(ack.event.type, "ACK")


class UpdateAcknowledgementSerializerTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.user = PersonUserFactory()

    def tearDown(self):
        connect_signals()

    def test_update_golden_path(self):
        incident = IncidentFactory()
        ack = incident.create_ack(self.user, expiration=None)
        self.assertFalse(ack.expiration)
        validated_data = {"expiration": timezone.now()}
        serializer = UpdateAcknowledgementSerializer()
        updated_ack = serializer.update(ack, validated_data)
        self.assertEqual(ack, updated_ack)
        self.assertTrue(updated_ack.expiration)

    def test_update_expired_ack_should_fail(self):
        incident = IncidentFactory()
        timestamp_in_the_past = timezone.now() - datetime.timedelta(days=30)
        ack = incident.create_ack(self.user, expiration=timestamp_in_the_past)
        validated_data = {"expiration": None}
        serializer = UpdateAcknowledgementSerializer()
        with self.assertRaises(serializers.ValidationError) as e:
            updated_ack = serializer.update(ack, validated_data)
