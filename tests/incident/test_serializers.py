from collections import OrderedDict
import datetime

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIRequestFactory
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from argus import incident

from argus.auth.factories import PersonUserFactory
from argus.incident.factories import IncidentTagRelationFactory, StatefulIncidentFactory
from argus.incident.models import IncidentTagRelation
from argus.incident.serializers import (
    AcknowledgementSerializer,
    EventSerializer,
    IncidentPureDeserializer,
    IncidentSerializer,
    IncidentTagRelationSerializer,
    TagSerializer,
    UpdateAcknowledgementSerializer,
)
from argus.util.datetime_utils import INFINITY_REPR
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
        incident = StatefulIncidentFactory()
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
        incident = StatefulIncidentFactory()
        ack = incident.create_ack(self.user, expiration=None)
        self.assertFalse(ack.expiration)
        validated_data = {"expiration": timezone.now()}
        serializer = UpdateAcknowledgementSerializer()
        updated_ack = serializer.update(ack, validated_data)
        self.assertEqual(ack, updated_ack)
        self.assertTrue(updated_ack.expiration)

    def test_update_expired_ack_should_fail(self):
        incident = StatefulIncidentFactory()
        timestamp_in_the_past = timezone.now() - datetime.timedelta(days=30)
        ack = incident.create_ack(self.user, expiration=timestamp_in_the_past)
        validated_data = {"expiration": None}
        serializer = UpdateAcknowledgementSerializer()
        with self.assertRaises(serializers.ValidationError) as e:
            updated_ack = serializer.update(ack, validated_data)


class IncidentSerializerTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_validate_stateful_incident_data(self):
        data = {
            "start_time": "2021-09-06T09:12:17.059Z",
            "level": 3,
            "tags": [],
        }
        serializer = IncidentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["end_time"], INFINITY_REPR)

    def test_validate_stateless_incident_data(self):
        data = {
            "start_time": "2021-09-06T09:12:17.059Z",
            "end_time": None,
            "level": 3,
            "tags": [],
        }
        serializer = IncidentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["end_time"], None)

    def test_validate_early_end_time(self):
        data = {
            "start_time": "2021-09-06T09:12:17.059Z",
            "end_time": "2020-09-06T09:12:17.059Z",
            "level": 3,
            "tags": [],
        }
        serializer = IncidentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_validate_erroneus_end_time(self):
        data = {
            "start_time": "2021-09-06T09:12:17.059Z",
            "end_time": "XXX",
            "level": 3,
            "tags": [],
        }
        serializer = IncidentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("end_time", serializer.errors)

    def test_incident_serializer_is_invalid_with_incorrect_ticket_url(self):
        data = {
            "start_time": "2021-09-06T09:12:17.059Z",
            "level": 3,
            "tags": [],
            "ticket_url": "invalid",
        }
        serializer = IncidentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("ticket_url", serializer.errors)


class IncidentPureDeserializerTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.url = "http://www.example.com/repository/issues/issue"
        self.incident_tag_relation = IncidentTagRelationFactory()
        self.tag = self.incident_tag_relation.tag
        self.incident = self.incident_tag_relation.incident

    def tearDown(self):
        connect_signals()

    def test_incident_pure_deserializer_is_valid_with_correct_input(self):
        data = {
            "details_url": self.url,
            "ticket_url": self.url,
            "level": 3,
            "tags": [],
        }
        serializer = IncidentPureDeserializer(instance=self.incident, data=data)
        self.assertTrue(serializer.is_valid())

    def test_incident_pure_deserializer_is_invalid_with_forbidden_fields(self):
        data = {
            "start_time": "2021-09-06T09:12:17.059Z",
        }
        serializer = IncidentPureDeserializer(instance=self.incident, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_time", serializer.errors)

    def test_incident_pure_deserializer_is_invalid_with_additional_fields(self):
        data = {
            "hello": "world",
        }
        serializer = IncidentPureDeserializer(instance=self.incident, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("hello", serializer.errors)

    def test_incident_pure_deserializer_is_invalid_with_incorrect_ticket_url(self):
        data = {
            "ticket_url": "invalid",
        }
        serializer = IncidentPureDeserializer(instance=self.incident, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("ticket_url", serializer.errors)

    def test_incident_pure_deserializer_can_delete_own_tags(self):
        data = {
            "details_url": self.url,
            "ticket_url": self.url,
            "level": 3,
            "tags": [],
        }
        serializer = IncidentPureDeserializer(instance=self.incident, data=data)
        serializer.is_valid()
        serializer.save(user=self.incident_tag_relation.added_by)
        self.assertFalse(self.incident.incident_tag_relations.exists())

    def test_incident_pure_deserializer_can_create_tags(self):
        new_tag = "a=b"
        data = {
            "details_url": self.url,
            "ticket_url": self.url,
            "level": 3,
            "tags": [
                {"tag": str(self.tag)},
                {"tag": new_tag},
            ],
        }
        serializer = IncidentPureDeserializer(instance=self.incident, data=data)
        serializer.is_valid()
        serializer.save(user=self.incident_tag_relation.added_by)
        tags = set([str(relation.tag) for relation in self.incident.incident_tag_relations.all()])
        self.assertEqual(tags, set([str(self.tag), new_tag]))

    def test_incident_pure_deserializer_cannot_delete_other_users_tags(self):
        data = {
            "details_url": self.url,
            "ticket_url": self.url,
            "level": 3,
            "tags": [],
        }
        serializer = IncidentPureDeserializer(instance=self.incident, data=data)
        serializer.is_valid()
        with self.assertRaises(serializers.ValidationError):
            serializer.save(user=self.incident.source.user)


class TagSerializerTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_tag_serializer_is_valid_with_correct_input(self):
        data = {
            "tag": "a=b",
        }
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["key"], "a")
        self.assertEqual(serializer.validated_data["value"], "b")

    def test_tag_serializer_is_invalid_with_wrong_form(self):
        data = {
            "tag": "a",
        }
        serializer = TagSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("tag", serializer.errors)

    def test_tag_serializer_is_invalid_with_empty_key(self):
        data = {
            "tag": "=b",
        }
        serializer = IncidentTagRelationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("tag", serializer.errors)


class IncidentTagRelationSerializerTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_incident_tag_relation_serializer_is_valid_with_correct_input(self):
        data = {
            "tag": "a=b",
        }
        serializer = IncidentTagRelationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["key"], "a")
        self.assertEqual(serializer.validated_data["value"], "b")

    def test_incident_tag_relation_serializer_is_invalid_without_equal_sign(self):
        data = {
            "tag": "a",
        }
        serializer = IncidentTagRelationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("tag", serializer.errors)

    def test_incident_tag_relation_serializer_is_invalid_with_empty_key(self):
        data = {
            "tag": "=b",
        }
        serializer = IncidentTagRelationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("tag", serializer.errors)


class EventSerializerTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.user = PersonUserFactory()
        self.request_factory = APIRequestFactory()

    def tearDown(self):
        connect_signals()

    def test_event_serializer_valid_with_correct_values(self):
        request = self.request_factory.post("/")
        request.user = self.user
        timestamp = timezone.now()
        data = {
            "actor": {},  # Forced to request.user
            "timestamp": timestamp.isoformat(),
            "type": "STA",  # Forced to ACK
            "description": "string",
        }
        serializer = EventSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())

    def test_event_serializer_sets_timestamp_if_not_set(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "actor": {},  # Forced to request.user
            "type": "STA",  # Forced to ACK
            "description": "string",
        }
        serializer = EventSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.validated_data["timestamp"])
