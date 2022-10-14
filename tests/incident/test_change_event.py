from django.test import tag

from rest_framework import status
from rest_framework.test import APITestCase
from argus.incident.factories import StatefulIncidentFactory
from argus.incident.models import Event
from argus.util.testing import disconnect_signals, connect_signals

from . import IncidentBasedAPITestCaseHelper


@tag("integration")
class ChangeEventTests(APITestCase, IncidentBasedAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()

        self.url = "http://www.example.com/repository/issues/issue"
        self.incident = StatefulIncidentFactory(level=1, ticket_url=self.url, details_url=self.url)

    def teardown(self):
        connect_signals()

    def test_change_event_is_created_on_level_changes(self):
        data = {
            "level": 2,
        }
        response = self.user1_rest_client.patch(
            path=f"/api/v2/incidents/{self.incident.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        change_events = self.incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)
        self.assertIn("Change: level 1 → 2", change_events_descriptions)

    def test_change_event_is_created_on_ticket_url_changes(self):
        new_ticket_url = "http://www.example.com/repository/issues/other-issue"
        response = self.user1_rest_client.patch(
            path=f"/api/v2/incidents/{self.incident.pk}/",
            data={
                "ticket_url": new_ticket_url,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        change_events = self.incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)
        self.assertIn(f"Change: ticket_url {self.url} → {new_ticket_url}", change_events_descriptions)

    def test_change_event_is_created_on_ticket_url_changes_for_ticket_url_endpoint(self):
        new_ticket_url = "http://www.example.com/repository/issues/other-issue"
        response = self.user1_rest_client.put(
            path=f"/api/v2/incidents/{self.incident.pk}/ticket_url/",
            data={
                "ticket_url": new_ticket_url,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        change_events = self.incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)
        self.assertIn(f"Change: ticket_url {self.url} → {new_ticket_url}", change_events_descriptions)

    def test_change_event_is_created_on_details_url_changes(self):
        new_details_url = "http://www.example.com/repository/issues/other-issue"
        response = self.user1_rest_client.patch(
            path=f"/api/v2/incidents/{self.incident.pk}/",
            data={
                "details_url": new_details_url,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        change_events = self.incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)
        self.assertIn(f"Change: details_url {self.url} → {new_details_url}", change_events_descriptions)

    def test_change_event_is_created_on_tag_changes(self):
        new_tag = "a=b"
        response = self.user1_rest_client.patch(
            path=f"/api/v2/incidents/{self.incident.pk}/",
            data={
                "tags": [{"tag": new_tag}],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        change_events = self.incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)
        self.assertIn(f"Change: tags [] → ['{new_tag}']", change_events_descriptions)
