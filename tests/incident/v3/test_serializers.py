from django.test import TestCase


from argus.incident.factories import (
    IncidentTagRelationFactory,
)
from argus.incident.v3.serializers import (
    IncidentPureDeserializer,
    IncidentSerializer,
    TagListSerializer,
)
from argus.util.datetime_utils import INFINITY_REPR
from argus.util.testing import disconnect_signals, connect_signals


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

    def test_incident_serializer_is_valid_with_correct_tags(self):
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": ["a=b"],
        }
        serializer = IncidentSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_incident_serializer_is_invalid_with_incorrect_tags(self):
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": ["a", "=b", 3],
        }
        serializer = IncidentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("tags", serializer.errors)


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

    def test_incident_pure_deserializer_can_create_tags(self):
        new_tag = "a=b"
        data = {
            "details_url": self.url,
            "ticket_url": self.url,
            "level": 3,
            "tags": [
                str(self.tag),
                new_tag,
            ],
        }
        serializer = IncidentPureDeserializer(instance=self.incident, data=data)
        serializer.is_valid()
        serializer.save(user=self.incident_tag_relation.added_by)
        tags = set([str(relation.tag) for relation in self.incident.incident_tag_relations.all()])
        self.assertEqual(tags, set([str(self.tag), new_tag]))


class TagListSerializerTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_tag_serializer_is_valid_with_correct_input(self):
        data = ["a=b"]
        serializer = TagListSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, data)

    def test_tag_serializer_is_invalid_with_wrong_form(self):
        data = ["a"]
        serializer = TagListSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        error_list = serializer.errors[0]
        self.assertIn("key-value", error_list[0])
        self.assertIn("at least 2", error_list[1])

    def test_tag_serializer_is_invalid_with_empty_key(self):
        data = ["=b"]
        serializer = TagListSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        error_list = serializer.errors[0]
        self.assertIn("key-value", error_list[0])
