from datetime import datetime, timedelta

from django.test import Client
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from argus.util import datetime_utils
from argus.util.testing import disconnect_signals, connect_signals
from argus.incident.factories import StatefulIncidentFactory, StatelessIncidentFactory
from argus.incident.models import Event, Incident
from . import IncidentBasedAPITestCaseHelper


class EventAPITests(APITestCase, IncidentBasedAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()

        super().init_test_objects()

        self.stateful_incident = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(weeks=1),
            end_time=timezone.now() + timedelta(weeks=1),
            source=self.source1,
        )
        self.stateful_incident.create_first_event()

        self.stateless_incident = StatelessIncidentFactory(source=self.source1)
        self.stateless_incident.create_first_event()

        self.events_url = lambda incident: reverse("v2:incident:incident-events", args=[incident.pk])

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

        response = client.post(self.events_url(self.stateful_incident), post_data)
        self._assert_response_field_invalid(response, "type")

        self.assertEqual(Event.objects.count(), event_count)
        self.stateful_incident.refresh_from_db()
        self.assertEqual(self.stateful_incident.end_time, original_end_time)

    def _assert_posting_event_succeeds(self, post_data: dict, client: Client):
        event_count = self.stateful_incident.events.count()

        response = client.post(self.events_url(self.stateful_incident), post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(self.stateful_incident.events.count(), event_count + 1)
        self.assertTrue(self.stateful_incident.events.filter(pk=response.data["pk"]).exists())
        self.assertEqual(response.data["incident"], self.stateful_incident.pk)

    def _assert_incident_is_closed_at_timestamp(self, incident: Incident, timestamp: datetime):
        incident.refresh_from_db()
        self.assertFalse(incident.open)
        self.assertEqual(incident.end_time, timestamp)

    def _assert_incident_is_open(self, incident: Incident):
        incident.refresh_from_db()
        self.assertTrue(incident.open)
        self.assertEqual(datetime_utils.make_naive(incident.end_time), datetime.max)

    def test_posting_close_and_reopen_events_properly_changes_stateful_incidents(self):
        # Test closing incident
        close_event_dict = self._create_event_dict(Event.Type.CLOSE)
        event_timestamp = close_event_dict["timestamp"]
        response = self.user1_rest_client.post(self.events_url(self.stateful_incident), close_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), event_timestamp)
        self._assert_incident_is_closed_at_timestamp(self.stateful_incident, event_timestamp)

        # It's illegal to close an already closed incident
        self._assert_posting_event_is_rejected_and_does_not_change_end_time(
            close_event_dict, self.stateful_incident.end_time, self.user1_rest_client
        )

        # Test reopening incident
        reopen_event_dict = self._create_event_dict(Event.Type.REOPEN)
        response = self.user1_rest_client.post(self.events_url(self.stateful_incident), reopen_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), reopen_event_dict["timestamp"])
        self._assert_incident_is_open(self.stateful_incident)

        # It's illegal to reopen an already opened incident
        self._assert_posting_event_is_rejected_and_does_not_change_end_time(
            reopen_event_dict, self.stateful_incident.end_time, self.user1_rest_client
        )

    def test_posting_end_and_restart_events_properly_changes_stateful_incidents(self):
        # Test ending incident
        end_event_dict = self._create_event_dict(Event.Type.INCIDENT_END)
        event_timestamp = end_event_dict["timestamp"]
        response = self.source1_rest_client.post(self.events_url(self.stateful_incident), end_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), event_timestamp)
        self._assert_incident_is_closed_at_timestamp(self.stateful_incident, event_timestamp)

        # Test restarting incident
        restart_event_dict = self._create_event_dict(Event.Type.INCIDENT_RESTART)
        response = self.source1_rest_client.post(self.events_url(self.stateful_incident), restart_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), restart_event_dict["timestamp"])
        self._assert_incident_is_open(self.stateful_incident)

        # Test ending again
        end_event_dict = self._create_event_dict(Event.Type.INCIDENT_END)
        event_timestamp = end_event_dict["timestamp"]
        response = self.source1_rest_client.post(self.events_url(self.stateful_incident), end_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), event_timestamp)
        self._assert_incident_is_closed_at_timestamp(self.stateful_incident, event_timestamp)

    def test_given_closed_incident_when_source_posts_end_then_records_event_without_state_change(self):
        # An end user posting a state-invalid event gets a 400; a source system does
        # not. Its event is recorded for the audit trail (201) but update_incident is
        # skipped, so the incident is unchanged. Here: END on an already-closed
        # incident must be accepted and recorded without re-touching end_time.
        count_before = self.stateful_incident.events.count()

        self.stateful_incident.end_time = timezone.now()
        self.stateful_incident.save(update_fields=["end_time"])

        end_event_dict = self._create_event_dict(Event.Type.INCIDENT_END)
        response = self.source1_rest_client.post(self.events_url(self.stateful_incident), end_event_dict)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self._assert_incident_is_closed_at_timestamp(self.stateful_incident, self.stateful_incident.end_time)
        self.stateful_incident.refresh_from_db()
        self.assertEqual(self.stateful_incident.events.count(), count_before + 1)

    def test_given_open_incident_when_source_posts_restart_then_records_event_without_state_change(self):
        # An end user posting a state-invalid event gets a 400; a source system does
        # not. Its event is recorded for the audit trail (201) but update_incident is
        # skipped, so the incident is unchanged. Here: RESTART on an already-open
        # incident must be accepted and recorded without re-touching end_time.
        self.stateful_incident.end_time = datetime_utils.INFINITY_REPR
        self.stateful_incident.save(update_fields=["end_time"])

        count_before = self.stateful_incident.events.count()

        restart_event_dict = self._create_event_dict(Event.Type.INCIDENT_RESTART)
        response = self.source1_rest_client.post(self.events_url(self.stateful_incident), restart_event_dict)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self._assert_incident_is_open(self.stateful_incident)
        self.stateful_incident.refresh_from_db()
        self.assertEqual(self.stateful_incident.events.count(), count_before + 1)

    def test_posting_close_and_reopen_events_does_not_change_stateless_incidents(self):
        def assert_incident_stateless():
            self.stateless_incident.refresh_from_db()
            self.assertFalse(self.stateless_incident.stateful)
            self.assertFalse(self.stateless_incident.open)

        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident), self._create_event_dict(Event.Type.CLOSE)
        )
        self._assert_response_field_invalid(response, "type")
        self.assertEqual(response.data["type"], "Cannot change the state of a stateless incident.")
        assert_incident_stateless()

        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident), self._create_event_dict(Event.Type.REOPEN)
        )
        self._assert_response_field_invalid(response, "type")
        self.assertEqual(response.data["type"], "Cannot change the state of a stateless incident.")
        assert_incident_stateless()

    def test_posting_end_and_restart_events_does_not_change_stateless_incidents_but_records_event(self):
        def assert_incident_stateless():
            self.stateless_incident.refresh_from_db()
            self.assertFalse(self.stateless_incident.stateful)
            self.assertFalse(self.stateless_incident.open)

        event_count = self.stateless_incident.events.count()

        response = self.source1_rest_client.post(
            self.events_url(self.stateless_incident), self._create_event_dict(Event.Type.INCIDENT_END)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert_incident_stateless()
        self.assertEqual(self.stateless_incident.events.count(), event_count + 1)

        response = self.source1_rest_client.post(
            self.events_url(self.stateless_incident), self._create_event_dict(Event.Type.INCIDENT_RESTART)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert_incident_stateless()
        self.assertEqual(self.stateless_incident.events.count(), event_count + 2)

    def test_posting_allowed_event_types_for_source_system_is_valid(self):
        def delete_start_event(incident: Incident):
            incident.start_event.delete()

        source_system_allowed_types_and_preconditions = {
            Event.Type.INCIDENT_START: delete_start_event,
            Event.Type.INCIDENT_END: lambda incident: None,
            Event.Type.INCIDENT_RESTART: lambda incident: None,
            Event.Type.OTHER: lambda incident: None,
        }
        for event_type, ensure_precondition in source_system_allowed_types_and_preconditions.items():
            with self.subTest(event_type=event_type):
                ensure_precondition(self.stateful_incident)
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
                ensure_precondition(self.stateful_incident)
                self._assert_posting_event_succeeds(self._create_event_dict(event_type), self.user1_rest_client)

    def test_posting_disallowed_event_types_for_source_system_is_invalid(self):
        original_end_time = self.stateful_incident.end_time

        source_system_disallowed_types = set(Event.Type.values) - Event.ALLOWED_TYPES_FOR_SOURCE_SYSTEMS
        for event_type in source_system_disallowed_types:
            with self.subTest(event_type=event_type):
                self._assert_posting_event_is_rejected_and_does_not_change_end_time(
                    self._create_event_dict(event_type), original_end_time, self.source1_rest_client
                )

    def test_posting_disallowed_event_types_for_end_user_is_invalid(self):
        original_end_time = self.stateful_incident.end_time

        end_user_disallowed_types = set(Event.Type.values) - Event.ALLOWED_TYPES_FOR_END_USERS
        for event_type in end_user_disallowed_types:
            with self.subTest(event_type=event_type):
                self._assert_posting_event_is_rejected_and_does_not_change_end_time(
                    self._create_event_dict(event_type), original_end_time, self.user1_rest_client
                )
