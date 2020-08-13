from datetime import datetime, timedelta

from django.test import Client
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from rest_framework.test import APITestCase

from argus.site import datetime_utils
from argus.site.utils import duplicate
from .test_incident import IncidentBasedAPITestCaseHelper
from ..models import Event, Incident


class EventAPITests(APITestCase, IncidentBasedAPITestCaseHelper):
    def setUp(self):
        super().init_test_objects()

        self.stateful_incident1 = Incident.objects.create(
            start_time=make_aware(datetime(2000, 1, 1)),
            end_time=timezone.now() + timedelta(weeks=1),
            source=self.source1,
            source_incident_id="1",
        )
        self.stateless_incident1 = duplicate(self.stateful_incident1, end_time=None, source_incident_id="2")

        self.events_url = lambda incident: reverse("incident:incident-events", args=[incident.pk])

    @staticmethod
    def _create_event_dict(event_type: str):
        return {
            "timestamp": timezone.now(),
            "type": event_type,
        }

    def _assert_response_field_invalid(self, response, field_name: str):
        self.assertEqual(response.status_code, 400)
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

    def test_posting_close_and_reopen_events_properly_changes_stateful_incidents(self):
        self.assertTrue(self.stateful_incident1.stateful)
        self.assertTrue(self.stateful_incident1.active)

        # Test closing incident
        close_event_dict = self._create_event_dict(Event.Type.CLOSE)
        event_timestamp = close_event_dict["timestamp"]
        response = self.user1_rest_client.post(self.events_url(self.stateful_incident1), close_event_dict)
        self.assertEqual(parse_datetime(response.data["timestamp"]), event_timestamp)
        self.stateful_incident1.refresh_from_db()
        self.assertFalse(self.stateful_incident1.active)
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
        self.assertTrue(self.stateful_incident1.active)
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
            self.assertFalse(self.stateless_incident1.active)

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
