from datetime import datetime, timedelta

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

        self.closed_incident = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1),
            source=self.source1,
        )
        self.closed_incident.create_first_event()
        Event.objects.create(
            incident=self.closed_incident,
            actor=self.user1,
            timestamp=self.closed_incident.end_time,
            type=Event.Type.CLOSE,
        )

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

    def test_when_posting_close_event_for_stateful_open_incident_then_incident_gets_closed(self):
        close_event_dict = {"timestamp": timezone.now(), "type": Event.Type.CLOSE}

        response = self.user1_rest_client.post(self.events_url(self.stateful_incident), close_event_dict)

        self.assertEqual(parse_datetime(response.data["timestamp"]), close_event_dict["timestamp"])
        self.stateful_incident.refresh_from_db()
        self.assertFalse(self.stateful_incident.open)
        self.assertEqual(self.stateful_incident.end_time, close_event_dict["timestamp"])

    def test_when_posting_close_event_for_stateful_closed_incident_then_end_time_does_not_change(self):
        close_event_dict = {"timestamp": timezone.now(), "type": Event.Type.CLOSE}
        original_end_time = self.closed_incident.end_time

        response = self.user1_rest_client.post(self.events_url(self.closed_incident), close_event_dict)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)
        self.assertEqual(response.data["type"].code, "invalid")

        self.closed_incident.refresh_from_db()
        self.assertEqual(self.closed_incident.end_time, original_end_time)

    def test_when_posting_reopen_event_for_stateful_closed_incident_then_incident_gets_reopened(self):
        reopen_event_dict = {"timestamp": timezone.now(), "type": Event.Type.REOPEN}
        response = self.user1_rest_client.post(self.events_url(self.closed_incident), reopen_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), reopen_event_dict["timestamp"])
        self.closed_incident.refresh_from_db()
        self.assertTrue(self.closed_incident.open)
        self.assertEqual(datetime_utils.make_naive(self.closed_incident.end_time), datetime.max)

    def test_when_posting_reopen_event_for_stateful_open_incident_then_return_bad_request(self):
        reopen_event_dict = {"timestamp": timezone.now(), "type": Event.Type.REOPEN}
        original_end_time = self.stateful_incident.end_time

        response = self.user1_rest_client.post(self.events_url(self.stateful_incident), reopen_event_dict)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)
        self.assertEqual(response.data["type"].code, "invalid")

        self.stateful_incident.refresh_from_db()
        self.assertEqual(self.stateful_incident.end_time, original_end_time)

    def test_when_posting_end_event_for_stateful_open_incident_then_incident_gets_closed(self):
        end_event_dict = {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_END}

        response = self.source1_rest_client.post(self.events_url(self.stateful_incident), end_event_dict)

        self.assertEqual(parse_datetime(response.data["timestamp"]), end_event_dict["timestamp"])
        self.stateful_incident.refresh_from_db()
        self.assertFalse(self.stateful_incident.open)
        self.assertEqual(self.stateful_incident.end_time, end_event_dict["timestamp"])

    def test_when_posting_restart_event_for_stateful_closed_incident_then_incident_gets_reopened(self):
        restart_event_dict = {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_RESTART}

        response = self.source1_rest_client.post(self.events_url(self.closed_incident), restart_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), restart_event_dict["timestamp"])
        self.closed_incident.refresh_from_db()
        self.assertTrue(self.closed_incident.open)
        self.assertEqual(datetime_utils.make_naive(self.closed_incident.end_time), datetime.max)

    def test_when_posting_end_event_for_ended_and_restarted_stateful_incident_then_incident_gets_closed(self):
        restarted_incident = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(hours=1),
            source=self.source1,
        )
        restarted_incident.create_first_event()
        Event.objects.create(
            incident=self.closed_incident,
            actor=self.source1_user,
            timestamp=timezone.now() - timedelta(minutes=30),
            type=Event.Type.INCIDENT_END,
        )
        Event.objects.create(
            incident=self.closed_incident,
            actor=self.source1_user,
            timestamp=timezone.now() - timedelta(minutes=10),
            type=Event.Type.INCIDENT_RESTART,
        )

        end_event_dict = {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_END}

        response = self.source1_rest_client.post(self.events_url(self.stateful_incident), end_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), end_event_dict["timestamp"])
        self.stateful_incident.refresh_from_db()
        self.assertFalse(self.stateful_incident.open)
        self.assertEqual(self.stateful_incident.end_time, end_event_dict["timestamp"])

    def test_posting_close_and_reopen_events_does_not_change_stateless_incidents(self):
        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident), {"timestamp": timezone.now(), "type": Event.Type.CLOSE}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)
        self.assertEqual(response.data["type"].code, "invalid")
        self.stateless_incident.refresh_from_db()
        self.assertFalse(self.stateless_incident.stateful)
        self.assertFalse(self.stateless_incident.open)

        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident), {"timestamp": timezone.now(), "type": Event.Type.REOPEN}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)
        self.assertEqual(response.data["type"].code, "invalid")
        self.stateless_incident.refresh_from_db()
        self.assertFalse(self.stateless_incident.stateful)
        self.assertFalse(self.stateless_incident.open)

    def test_posting_end_and_restart_events_does_not_change_stateless_incidents(self):
        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident), {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_END}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)
        self.assertEqual(response.data["type"].code, "invalid")
        self.stateless_incident.refresh_from_db()
        self.assertFalse(self.stateless_incident.stateful)
        self.assertFalse(self.stateless_incident.open)

        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident), {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_RESTART}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)
        self.assertEqual(response.data["type"].code, "invalid")
        self.stateless_incident.refresh_from_db()
        self.assertFalse(self.stateless_incident.stateful)
        self.assertFalse(self.stateless_incident.open)

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
                event_count = self.stateful_incident.events.count()

                response = self.source1_rest_client.post(
                    self.events_url(self.stateful_incident),
                    {"timestamp": timezone.now(), "type": event_type},
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                self.assertEqual(self.stateful_incident.events.count(), event_count + 1)
                self.assertTrue(self.stateful_incident.events.filter(pk=response.data["pk"]).exists())
                self.assertEqual(response.data["incident"], self.stateful_incident.pk)

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
                event_count = self.stateful_incident.events.count()

                response = self.user1_rest_client.post(
                    self.events_url(self.stateful_incident),
                    {"timestamp": timezone.now(), "type": event_type},
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                self.assertEqual(self.stateful_incident.events.count(), event_count + 1)
                self.assertTrue(self.stateful_incident.events.filter(pk=response.data["pk"]).exists())
                self.assertEqual(response.data["incident"], self.stateful_incident.pk)

    def test_posting_disallowed_event_types_for_source_system_is_invalid(self):
        original_end_time = self.stateful_incident.end_time

        source_system_disallowed_types = set(Event.Type.values) - Event.ALLOWED_TYPES_FOR_SOURCE_SYSTEMS
        for event_type in source_system_disallowed_types:
            with self.subTest(event_type=event_type):
                event_count = Event.objects.count()

                response = self.source1_rest_client.post(
                    self.events_url(self.stateful_incident), {"timestamp": timezone.now(), "type": event_type}
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("type", response.data)
                self.assertEqual(response.data["type"].code, "invalid")

                self.assertEqual(Event.objects.count(), event_count)
                self.stateful_incident.refresh_from_db()
                self.assertEqual(self.stateful_incident.end_time, original_end_time)

    def test_posting_disallowed_event_types_for_end_user_is_invalid(self):
        original_end_time = self.stateful_incident.end_time

        end_user_disallowed_types = set(Event.Type.values) - Event.ALLOWED_TYPES_FOR_END_USERS
        for event_type in end_user_disallowed_types:
            with self.subTest(event_type=event_type):
                event_count = Event.objects.count()

                response = self.user1_rest_client.post(
                    self.events_url(self.stateful_incident), {"timestamp": timezone.now(), "type": event_type}
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("type", response.data)
                self.assertEqual(response.data["type"].code, "invalid")

                self.assertEqual(Event.objects.count(), event_count)
                self.stateful_incident.refresh_from_db()
                self.assertEqual(self.stateful_incident.end_time, original_end_time)
