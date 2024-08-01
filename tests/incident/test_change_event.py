from django.test import override_settings, tag

from rest_framework import status
from rest_framework.test import APITestCase
from argus.incident.factories import StatefulIncidentFactory
from argus.incident.models import Event, ChangeEvent
from argus.util.testing import disconnect_signals, connect_signals

from . import IncidentBasedAPITestCaseHelper


# format_description tests here, one for each outlier (now metadata), one for
# the normal ones


@tag("integration")
class ChangeEventTests(APITestCase, IncidentBasedAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()

        self.url = "http://www.example.com/repository/issues/issue"
        self.incident = StatefulIncidentFactory(
            level=1,
            ticket_url=self.url,
            details_url=self.url,
            description="old_description",
            source=self.source1,
        )

    def teardown(self):
        connect_signals()

    def test_change_event_is_created_on_level_changes(self):
        data = {
            "level": 2,
        }
        description = ChangeEvent.format_description("level", 1, 2)
        response = self.user1_rest_client.patch(
            path=f"/api/v2/incidents/{self.incident.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        change_events = self.incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)
        self.assertIn(description, change_events_descriptions)
        self.assertEqual(change_events.get(description=description).actor, self.user1)

    def test_change_event_is_created_on_ticket_url_changes(self):
        new_ticket_url = "http://www.example.com/repository/issues/other-issue"
        description = ChangeEvent.format_description("ticket_url", self.url, new_ticket_url)

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
        self.assertIn(description, change_events_descriptions)
        self.assertEqual(change_events.get(description=description).actor, self.user1)

    def test_change_event_is_created_on_ticket_url_changes_for_ticket_url_endpoint(self):
        new_ticket_url = "http://www.example.com/repository/issues/other-issue"
        description = ChangeEvent.format_description("ticket_url", self.url, new_ticket_url)

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
        self.assertIn(description, change_events_descriptions)
        self.assertEqual(change_events.get(description=description).actor, self.user1)

    @override_settings(
        TICKET_PLUGIN="argus.incident.ticket.dummy.DummyPlugin",
    )
    def test_change_event_is_created_on_ticket_url_changes_for_automatic_ticket_url_endpoint(self):
        incident = StatefulIncidentFactory(ticket_url="", source=self.source1)
        response = self.user1_rest_client.put(
            path=f"/api/v2/incidents/{incident.pk}/automatic-ticket/",
            data={},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        change_events = incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)

        new_ticket_url = response.data["ticket_url"]
        description = ChangeEvent.format_description("ticket_url", "", new_ticket_url)
        self.assertIn(description, change_events_descriptions)
        self.assertEqual(change_events.get(description=description).actor, self.user1)

    def test_change_event_is_created_on_details_url_changes(self):
        new_details_url = "http://www.example.com/repository/issues/other-issue"
        description = ChangeEvent.format_description("details_url", self.url, new_details_url)

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
        self.assertIn(description, change_events_descriptions)
        self.assertEqual(change_events.get(description=description).actor, self.user1)

    def test_change_event_is_created_on_tag_changes(self):
        new_tag = "a=b"
        description = ChangeEvent.format_description("tags", "[]", [new_tag])

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
        self.assertIn(description, change_events_descriptions)
        self.assertEqual(change_events.get(description=description).actor, self.user1)

    def test_change_event_is_created_on_metadata_changes(self):
        new_metadata = {1: 2}
        description = ChangeEvent.format_description("metadata", {}, new_metadata)

        response = self.user1_rest_client.patch(
            path=f"/api/v2/incidents/{self.incident.pk}/",
            data={
                "metadata": new_metadata,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        change_events = self.incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)
        self.assertIn(description, change_events_descriptions)
        self.assertEqual(change_events.get(description=description).actor, self.user1)

    def test_change_event_is_created_on_description_changes(self):
        data = {
            "description": "new_description",
        }
        description = ChangeEvent.format_description("description", "old_description", "new_description")
        response = self.user1_rest_client.patch(
            path=f"/api/v2/incidents/{self.incident.pk}/",
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        change_events = self.incident.events.filter(type=Event.Type.INCIDENT_CHANGE)
        change_events_descriptions = [event.description for event in change_events]
        self.assertTrue(change_events)
        self.assertIn(description, change_events_descriptions)
        self.assertEqual(change_events.get(description=description).actor, self.user1)
