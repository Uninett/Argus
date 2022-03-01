from datetime import datetime, timedelta

from django.db.models import signals
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from argus.util import datetime_utils
from argus.util.utils import duplicate
from argus.util.testing import disconnect_signals, connect_signals
from argus.incident.factories import StatefulIncidentFactory, SourceSystemFactory
from argus.incident.models import Event, Incident
from . import IncidentBasedAPITestCaseHelper


class EventAPITests(APITestCase, IncidentBasedAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()

        super().init_test_objects()

        self.stateful_incident1 = StatefulIncidentFactory(
            start_time=make_aware(datetime(2000, 1, 1)),
            end_time=timezone.now() + timedelta(weeks=1),
            source=self.source1,
            source_incident_id="1",
        )
        self.stateless_incident1 = duplicate(self.stateful_incident1, end_time=None, source_incident_id="2")

        self.events_url = lambda incident: reverse("v1:incident:incident-events", args=[incident.pk])

    def tearDown(self):
        connect_signals()

    @staticmethod
    def _create_event_dict(event_type: str):
        return {
            "timestamp": timezone.now(),
            "type": event_type,
        }

    def _assert_response_field_invalid(self, response, field_name: str):
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(field_name, response.data)
        self.assertEqual(response.data[field_name].code, "invalid")

    def _assert_posting_event_is_rejected_and_does_not_change_end_time(
        self, post_data: dict, original_end_time: datetime, client: Client
    ):
        event_count = Event.objects.count()

        response = client.post(self.events_url(self.stateful_incident1), post_data)
        self._assert_response_field_invalid(response, "type")

        self.assertEqual(Event.objects.count(), event_count)
        self.stateful_incident1.refresh_from_db()
        self.assertEqual(self.stateful_incident1.end_time, original_end_time)

    def _assert_posting_event_succeeds(self, post_data: dict, client: Client):
        event_count = self.stateful_incident1.events.count()

        response = client.post(self.events_url(self.stateful_incident1), post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(self.stateful_incident1.events.count(), event_count + 1)
        self.assertTrue(self.stateful_incident1.events.filter(pk=response.data["pk"]).exists())
        self.assertEqual(response.data["incident"], self.stateful_incident1.pk)

    def test_posting_close_and_reopen_events_properly_changes_stateful_incidents(self):
        self.assertTrue(self.stateful_incident1.stateful)
        self.assertTrue(self.stateful_incident1.open)

        # Test closing incident
        close_event_dict = self._create_event_dict(Event.Type.CLOSE)
        event_timestamp = close_event_dict["timestamp"]
        response = self.user1_rest_client.post(self.events_url(self.stateful_incident1), close_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), event_timestamp)
        self.stateful_incident1.refresh_from_db()
        self.assertFalse(self.stateful_incident1.open)
        set_end_time = self.stateful_incident1.end_time
        self.assertEqual(set_end_time, event_timestamp)

        # It's illegal to close an already closed incident
        self._assert_posting_event_is_rejected_and_does_not_change_end_time(
            close_event_dict, set_end_time, self.user1_rest_client
        )

        # Test reopening incident
        reopen_event_dict = self._create_event_dict(Event.Type.REOPEN)
        response = self.user1_rest_client.post(self.events_url(self.stateful_incident1), reopen_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), reopen_event_dict["timestamp"])
        self.stateful_incident1.refresh_from_db()
        self.assertTrue(self.stateful_incident1.open)
        set_end_time = self.stateful_incident1.end_time
        self.assertEqual(datetime_utils.make_naive(set_end_time), datetime.max)

        # It's illegal to reopen an already opened incident
        self._assert_posting_event_is_rejected_and_does_not_change_end_time(
            reopen_event_dict, set_end_time, self.user1_rest_client
        )

    def test_posting_close_and_reopen_events_does_not_change_stateless_incidents(self):
        def assert_incident_stateless():
            self.stateless_incident1.refresh_from_db()
            self.assertFalse(self.stateless_incident1.stateful)
            self.assertFalse(self.stateless_incident1.open)

        assert_incident_stateless()
        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident1), self._create_event_dict(Event.Type.CLOSE)
        )
        self._assert_response_field_invalid(response, "type")
        assert_incident_stateless()

        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident1), self._create_event_dict(Event.Type.REOPEN)
        )
        self._assert_response_field_invalid(response, "type")
        assert_incident_stateless()

    def test_posting_allowed_event_types_for_source_system_is_valid(self):
        def delete_start_event(incident: Incident):
            incident.start_event.delete()

        source_system_allowed_types_and_preconditions = {
            Event.Type.INCIDENT_START: delete_start_event,
            Event.Type.INCIDENT_END: lambda incident: None,
            Event.Type.OTHER: lambda incident: None,
        }
        for event_type, ensure_precondition in source_system_allowed_types_and_preconditions.items():
            with self.subTest(event_type=event_type):
                ensure_precondition(self.stateful_incident1)
                self._assert_posting_event_succeeds(self._create_event_dict(event_type), self.source1_rest_client)

    def test_posting_allowed_event_types_for_end_user_is_valid(self):
        def set_end_time_to(end_time):
            def set_end_time(incident: Incident):
                incident.end_time = end_time
                incident.save()

            return set_end_time

        end_user_allowed_types_and_preconditions = {
            Event.Type.CLOSE: set_end_time_to("infinity"),
            Event.Type.REOPEN: set_end_time_to(timezone.now()),
            Event.Type.OTHER: lambda incident: None,
        }
        for event_type, ensure_precondition in end_user_allowed_types_and_preconditions.items():
            with self.subTest(event_type=event_type):
                ensure_precondition(self.stateful_incident1)
                self._assert_posting_event_succeeds(self._create_event_dict(event_type), self.user1_rest_client)

    def test_posting_disallowed_event_types_for_source_system_is_invalid(self):
        original_end_time = self.stateful_incident1.end_time

        source_system_disallowed_types = set(Event.Type.values) - Event.ALLOWED_TYPES_FOR_SOURCE_SYSTEMS
        for event_type in source_system_disallowed_types:
            with self.subTest(event_type=event_type):
                self._assert_posting_event_is_rejected_and_does_not_change_end_time(
                    self._create_event_dict(event_type), original_end_time, self.source1_rest_client
                )

    def test_posting_disallowed_event_types_for_end_user_is_invalid(self):
        original_end_time = self.stateful_incident1.end_time

        end_user_disallowed_types = set(Event.Type.values) - Event.ALLOWED_TYPES_FOR_END_USERS
        for event_type in end_user_disallowed_types:
            with self.subTest(event_type=event_type):
                self._assert_posting_event_is_rejected_and_does_not_change_end_time(
                    self._create_event_dict(event_type), original_end_time, self.user1_rest_client
                )


class EventSignalTests(APITestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_event_has_description(self):
        source_incident_id = "abcknekkebrod"
        incident = Incident.objects.create(
            start_time=timezone.now(),
            end_time=datetime_utils.INFINITY_REPR,
            source_incident_id=source_incident_id,
            source=SourceSystemFactory(),
            description=f"Incident #{source_incident_id} created for testing",
        )
        event_start = incident.events.filter(type=Event.Type.INCIDENT_START)

        self.assertTrue(event_start)
        self.assertEqual(incident.description, incident.events.get(type="STA").description)


class StatelessEventTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_new_stateless_incident_has_stateless_event(self):
        source_incident_id = "abcknekkebrod"
        incident = Incident.objects.create(
            start_time=timezone.now(),
            end_time=None,
            source_incident_id=source_incident_id,
            source=SourceSystemFactory(),
            description=f"Incident #{source_incident_id} created for testing",
        )
        event_stateless = incident.events.filter(type=Event.Type.STATELESS)
        self.assertEqual(1, event_stateless.count())
