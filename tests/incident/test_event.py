from datetime import datetime, timedelta

from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from argus.util import datetime_utils
from argus.util.testing import disconnect_signals, connect_signals
from argus.incident.factories import StatefulIncidentFactory, StatelessIncidentFactory
from argus.incident.models import Event
from . import IncidentBasedAPITestCaseHelper


class EventAPIStatefulIncidentTests(APITestCase, IncidentBasedAPITestCaseHelper):
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

        self.open_incident = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(weeks=1),
            source=self.source1,
        )
        self.open_incident.create_first_event()

        self.events_url = lambda incident: reverse("v2:incident:incident-events", args=[incident.pk])

    def tearDown(self):
        connect_signals()

    def test_when_posting_close_event_for_open_incident_then_incident_gets_closed(self):
        close_event_dict = {"timestamp": timezone.now(), "type": Event.Type.CLOSE}

        response = self.user1_rest_client.post(self.events_url(self.open_incident), close_event_dict)

        self.assertEqual(parse_datetime(response.data["timestamp"]), close_event_dict["timestamp"])
        self.open_incident.refresh_from_db()
        self.assertFalse(self.open_incident.open)
        self.assertEqual(self.open_incident.end_time, close_event_dict["timestamp"])

    def test_when_posting_close_event_for_closed_incident_then_end_time_does_not_change(self):
        close_event_dict = {"timestamp": timezone.now(), "type": Event.Type.CLOSE}
        original_end_time = self.closed_incident.end_time

        response = self.user1_rest_client.post(self.events_url(self.closed_incident), close_event_dict)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)
        self.assertEqual(response.data["type"].code, "invalid")

        self.closed_incident.refresh_from_db()
        self.assertEqual(self.closed_incident.end_time, original_end_time)

    def test_when_posting_reopen_event_for_closed_incident_then_incident_gets_reopened(self):
        reopen_event_dict = {"timestamp": timezone.now(), "type": Event.Type.REOPEN}
        response = self.user1_rest_client.post(self.events_url(self.closed_incident), reopen_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), reopen_event_dict["timestamp"])
        self.closed_incident.refresh_from_db()
        self.assertTrue(self.closed_incident.open)
        self.assertEqual(datetime_utils.make_naive(self.closed_incident.end_time), datetime.max)

    def test_when_posting_reopen_event_for_open_incident_then_return_bad_request(self):
        reopen_event_dict = {"timestamp": timezone.now(), "type": Event.Type.REOPEN}
        original_end_time = self.open_incident.end_time

        response = self.user1_rest_client.post(self.events_url(self.open_incident), reopen_event_dict)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)
        self.assertEqual(response.data["type"].code, "invalid")

        self.open_incident.refresh_from_db()
        self.assertEqual(self.open_incident.end_time, original_end_time)

    def test_when_posting_end_event_for_open_incident_then_incident_gets_closed(self):
        end_event_dict = {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_END}

        response = self.source1_rest_client.post(self.events_url(self.open_incident), end_event_dict)

        self.assertEqual(parse_datetime(response.data["timestamp"]), end_event_dict["timestamp"])
        self.open_incident.refresh_from_db()
        self.assertFalse(self.open_incident.open)
        self.assertEqual(self.open_incident.end_time, end_event_dict["timestamp"])

    def test_when_posting_restart_event_for_closed_incident_then_incident_gets_reopened(self):
        restart_event_dict = {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_RESTART}

        response = self.source1_rest_client.post(self.events_url(self.closed_incident), restart_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), restart_event_dict["timestamp"])
        self.closed_incident.refresh_from_db()
        self.assertTrue(self.closed_incident.open)
        self.assertEqual(datetime_utils.make_naive(self.closed_incident.end_time), datetime.max)

    def test_when_posting_end_event_for_ended_and_restarted_incident_then_incident_gets_closed(self):
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

        response = self.source1_rest_client.post(self.events_url(self.open_incident), end_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), end_event_dict["timestamp"])
        self.open_incident.refresh_from_db()
        self.assertFalse(self.open_incident.open)
        self.assertEqual(self.open_incident.end_time, end_event_dict["timestamp"])

    def test_given_closed_incident_when_source_posts_end_then_records_event_without_state_change(self):
        # An end user posting a state-invalid event gets a 400; a source system does
        # not. Its event is recorded for the audit trail (201) but update_incident is
        # skipped, so the incident is unchanged. Here: END on an already-closed
        # incident must be accepted and recorded without re-touching end_time.
        count_before = self.closed_incident.events.count()
        original_timestamp = self.closed_incident.end_time

        end_event_dict = {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_END}
        response = self.source1_rest_client.post(self.events_url(self.closed_incident), end_event_dict)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.closed_incident.refresh_from_db()
        self.assertFalse(self.closed_incident.open)
        self.assertEqual(self.closed_incident.end_time, original_timestamp)
        self.assertEqual(self.closed_incident.events.count(), count_before + 1)

    def test_given_open_incident_when_source_posts_restart_then_records_event_without_state_change(self):
        # An end user posting a state-invalid event gets a 400; a source system does
        # not. Its event is recorded for the audit trail (201) but update_incident is
        # skipped, so the incident is unchanged. Here: RESTART on an already-open
        # incident must be accepted and recorded without re-touching end_time.
        count_before = self.open_incident.events.count()

        restart_event_dict = {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_RESTART}
        response = self.source1_rest_client.post(self.events_url(self.open_incident), restart_event_dict)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.open_incident.refresh_from_db()
        self.assertTrue(self.open_incident.open)
        self.assertEqual(datetime_utils.make_naive(self.open_incident.end_time), datetime.max)
        self.assertEqual(self.open_incident.events.count(), count_before + 1)


class EventAPIStatelessIncidentTests(APITestCase, IncidentBasedAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()

        super().init_test_objects()

        self.stateless_incident = StatelessIncidentFactory(source=self.source1)
        self.stateless_incident.create_first_event()

        self.events_url = lambda incident: reverse("v2:incident:incident-events", args=[incident.pk])

    def test_when_posting_close_event_for_stateless_incident_then_incident_does_not_change(self):
        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident), {"timestamp": timezone.now(), "type": Event.Type.CLOSE}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["type"], "Cannot change the state of a stateless incident.")
        self.stateless_incident.refresh_from_db()
        self.assertFalse(self.stateless_incident.stateful)
        self.assertFalse(self.stateless_incident.open)

    def test_when_posting_reopen_event_then_incident_does_not_change(self):
        response = self.user1_rest_client.post(
            self.events_url(self.stateless_incident), {"timestamp": timezone.now(), "type": Event.Type.REOPEN}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["type"], "Cannot change the state of a stateless incident.")
        self.stateless_incident.refresh_from_db()
        self.assertFalse(self.stateless_incident.stateful)
        self.assertFalse(self.stateless_incident.open)

    def test_when_posting_end_event_then_incident_does_not_change_and_event_is_recorded(self):
        event_count = self.stateless_incident.events.count()

        response = self.source1_rest_client.post(
            self.events_url(self.stateless_incident), {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_END}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.stateless_incident.refresh_from_db()
        self.assertFalse(self.stateless_incident.stateful)
        self.assertFalse(self.stateless_incident.open)
        self.assertEqual(self.stateless_incident.events.count(), event_count + 1)

    def test_when_posting_restart_event_then_incident_does_not_change_and_event_is_recorded(self):
        event_count = self.stateless_incident.events.count()

        response = self.source1_rest_client.post(
            self.events_url(self.stateless_incident), {"timestamp": timezone.now(), "type": Event.Type.INCIDENT_RESTART}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.stateless_incident.refresh_from_db()
        self.assertFalse(self.stateless_incident.stateful)
        self.assertFalse(self.stateless_incident.open)
        self.assertEqual(self.stateless_incident.events.count(), event_count + 1)


class EventAPISourceSystemUserTests(APITestCase, IncidentBasedAPITestCaseHelper):
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

        self.open_incident = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(weeks=1),
            source=self.source1,
        )
        self.open_incident.create_first_event()

        self.open_incident_without_start_event = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(weeks=1),
            source=self.source1,
        )

        self.events_url = lambda incident: reverse("v2:incident:incident-events", args=[incident.pk])

    def tearDown(self):
        connect_signals()

    def test_when_posting_allowed_event_types_for_source_system_user_then_event_is_created(self):
        source_system_allowed_types_and_incidents = {
            Event.Type.INCIDENT_START: self.open_incident_without_start_event,
            Event.Type.INCIDENT_END: self.open_incident,
            Event.Type.INCIDENT_RESTART: self.closed_incident,
            Event.Type.OTHER: self.open_incident,
        }
        for event_type, incident in source_system_allowed_types_and_incidents.items():
            with self.subTest(event_type=event_type):
                event_count = incident.events.count()

                response = self.source1_rest_client.post(
                    self.events_url(incident),
                    {"timestamp": timezone.now(), "type": event_type},
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                self.assertEqual(incident.events.count(), event_count + 1)
                self.assertTrue(incident.events.filter(pk=response.data["pk"]).exists())
                self.assertEqual(response.data["incident"], incident.pk)

    def test_when_posting_disallowed_event_types_for_source_system_user_then_return_bad_request(self):
        original_end_time = self.open_incident.end_time

        source_system_disallowed_types = set(Event.Type.values) - Event.ALLOWED_TYPES_FOR_SOURCE_SYSTEMS
        for event_type in source_system_disallowed_types:
            with self.subTest(event_type=event_type):
                event_count = self.open_incident.events.count()

                response = self.source1_rest_client.post(
                    self.events_url(self.open_incident), {"timestamp": timezone.now(), "type": event_type}
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("type", response.data)
                self.assertEqual(response.data["type"].code, "invalid")

                self.assertEqual(self.open_incident.events.count(), event_count)
                self.open_incident.refresh_from_db()
                self.assertEqual(self.open_incident.end_time, original_end_time)


class EventAPIEndUserTests(APITestCase, IncidentBasedAPITestCaseHelper):
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

        self.open_incident = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(weeks=1),
            source=self.source1,
        )
        self.open_incident.create_first_event()

        self.events_url = lambda incident: reverse("v2:incident:incident-events", args=[incident.pk])

    def tearDown(self):
        connect_signals()

    def test_when_posting_allowed_event_types_for_end_user_then_event_is_created(self):
        end_user_allowed_types_and_incidents = {
            Event.Type.CLOSE: self.open_incident,
            Event.Type.REOPEN: self.closed_incident,
            Event.Type.OTHER: self.open_incident,
        }
        for event_type, incident in end_user_allowed_types_and_incidents.items():
            with self.subTest(event_type=event_type):
                event_count = incident.events.count()

                response = self.user1_rest_client.post(
                    self.events_url(incident),
                    {"timestamp": timezone.now(), "type": event_type},
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                self.assertEqual(incident.events.count(), event_count + 1)
                self.assertTrue(incident.events.filter(pk=response.data["pk"]).exists())
                self.assertEqual(response.data["incident"], incident.pk)

    def test_when_posting_disallowed_event_types_for_end_user_then_return_bad_request(self):
        original_end_time = self.open_incident.end_time

        end_user_disallowed_types = set(Event.Type.values) - Event.ALLOWED_TYPES_FOR_END_USERS
        for event_type in end_user_disallowed_types:
            with self.subTest(event_type=event_type):
                event_count = self.open_incident.events.count()

                response = self.user1_rest_client.post(
                    self.events_url(self.open_incident), {"timestamp": timezone.now(), "type": event_type}
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("type", response.data)
                self.assertEqual(response.data["type"].code, "invalid")

                self.assertEqual(self.open_incident.events.count(), event_count)
                self.open_incident.refresh_from_db()
                self.assertEqual(self.open_incident.end_time, original_end_time)
