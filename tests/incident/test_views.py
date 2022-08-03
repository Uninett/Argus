from django.urls import reverse
from django.test import TestCase, RequestFactory

from rest_framework import serializers, status, versioning
from rest_framework.test import APITestCase

from argus.auth.factories import AdminUserFactory, SourceUserFactory
from argus.incident.factories import SourceSystemTypeFactory, SourceSystemFactory, StatefulIncidentFactory
from argus.incident.models import Acknowledgement, Event, Incident, SourceSystem, SourceSystemType, Tag
from argus.incident.views import EventViewSet
from argus.util.testing import disconnect_signals, connect_signals


class EventViewSetTestCase(TestCase):
    def setUp(self):
        disconnect_signals()
        source_type = SourceSystemTypeFactory()
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(type=source_type, user=source_user)

    def tearDown(self):
        connect_signals()

    def test_validate_event_type_for_incident_acknowledge_raises_validation_error(self):
        incident = StatefulIncidentFactory(source=self.source)
        viewfactory = RequestFactory()
        request = viewfactory.get(path=f"/api/v1/incidents/{incident.pk}/events/")
        request.versioning_scheme = versioning.NamespaceVersioning()
        request.version = "v1"
        view = EventViewSet()
        view.request = request
        with self.assertRaises(serializers.ValidationError):
            view.validate_event_type_for_incident(event_type=Event.Type.ACKNOWLEDGE, incident=incident)


class IncidentViewSetV1TestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        disconnect_signals()
        source_type = SourceSystemTypeFactory()
        cls.user = SourceUserFactory()
        cls.source = SourceSystemFactory(type=source_type, user=cls.user)
        cls.admin = AdminUserFactory()

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    @classmethod
    def tearDownClass(cls):
        connect_signals()

    def add_incident(self, description="incident"):
        data = {
            "start_time": "2022-05-24T13:07:29.254Z",
            "end_time": "2022-05-24T13:07:29.254Z",
            "description": description,
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v1/incidents/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        return response.data["pk"]

    def add_acknowledgement(self, incident_pk, description="acknowledgement"):
        data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "type": "STA",
                "description": description,
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/acks/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        return response.data["pk"]

    def add_event(self, incident_pk, description="event"):
        data = {
            "timestamp": "2022-08-02T13:04:03.529Z",
            "type": "OTH",
            "description": description,
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/events/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        return response.data["pk"]

    def test_no_incidents_returns_empty_list(self):
        response = self.client.get(path="/api/v1/incidents/")
        self.assertFalse(Incident.objects.exists())
        self.assertEqual(response.status_code, 200)
        # Paging, so check "results"
        self.assertEqual(response.data["results"], [])

    def test_get_incident_returns_all_incidents(self):
        incident_pk = self.add_incident()
        response = self.client.get(path="/api/v1/incidents/")
        self.assertTrue(Incident.objects.exists())
        self.assertEqual(response.status_code, 200)
        # Paging, so check "results"
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_posting_incident_with_tag_should_create_incident_and_tag(self):
        # Start with no incidents or tags
        self.assertFalse(Incident.objects.exists())
        self.assertFalse(Tag.objects.exists())
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v1/incidents/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        # Check that we have made the correct Incident
        self.assertEqual(response.data["description"], data["description"])
        self.assertTrue(Incident.objects.exists())
        obj = Incident.objects.get()
        self.assertEqual(obj.description, data["description"])
        # Check that we have made the correct Tag
        self.assertTrue(Tag.objects.exists())
        tag = Tag.objects.get()
        self.assertEqual(obj.tags, [tag])
        self.assertEqual(str(tag), data["tags"][0]["tag"])

    def test_get_incident_by_pk_returns_correct_incident(self):
        incident_pk = self.add_incident()
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pk"], incident_pk)

    def test_incident_can_properly_change_level(self):
        incident_pk = self.add_incident()
        incident_path = reverse("v1:incident:incident-detail", args=[incident_pk])
        response = self.client.put(
            path=incident_path,
            data={
                "tags": [{"tag": "a=b"}],
                "level": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(pk=incident_pk).level, 2)

    def test_incident_acks_returns_correct_acks(self):
        incident_pk = self.add_incident()
        ack_pk = self.add_acknowledgement(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/acks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["event"]["pk"], ack_pk)
        self.assertEqual(response.data[0]["event"]["type"]["value"], "ACK")

    def test_posting_acknowledgement_creates_acknowledgement(self):
        incident_pk = self.add_incident()
        self.assertFalse(Acknowledgement.objects.exists())
        data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "type": "STA",
                "description": "acknowledgement",
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/acks/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")
        self.assertEqual(response.data["event"]["description"], data["event"]["description"])

    def test_get_acknowledgement_by_pk_returns_correct_acknowledgement(self):
        incident_pk = self.add_incident()
        ack_pk = self.add_acknowledgement(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/acks/{ack_pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["event"]["pk"], ack_pk)
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")

    def test_incident_events_returns_correct_events_of_incident(self):
        incident_pk = self.add_incident()
        event_pk = self.add_event(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["pk"], event_pk)
        self.assertEqual(response.data[0]["type"]["value"], "OTH")

    def test_posting_event_creates_event(self):
        incident_pk = self.add_incident()
        self.assertFalse(Acknowledgement.objects.exists())
        data = {
            "timestamp": "2022-08-02T13:45:44.056Z",
            "type": "OTH",
            "description": "event",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/events/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["type"]["value"], "OTH")
        self.assertEqual(response.data["description"], data["description"])

    def test_get_event_by_pk_returns_correct_event(self):
        incident_pk = self.add_incident()
        event_pk = self.add_event(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/events/{event_pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pk"], event_pk)
        self.assertEqual(response.data["type"]["value"], "OTH")

    def test_incident_tags_returns_correct_tags(self):
        # Automatically creates tag
        incident_pk = self.add_incident()
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/tags/")
        tag = str(Tag.objects.first())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["tag"], tag)

    def test_posting_tag_creates_tag(self):
        # Automatically creates tag
        incident_pk = self.add_incident()
        self.assertEqual(Tag.objects.count(), 1)
        data = {
            "tag": "c=d",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/tags/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["tag"], data["tag"])
        self.assertEqual(Tag.objects.count(), 2)

    def test_get_tag_by_tag_returns_correct_tag(self):
        # Automatically creates tag
        incident_pk = self.add_incident()
        tag = str(Tag.objects.first())
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/tags/{tag}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tag"], tag)

    def test_delete_tag_deletes_tag(self):
        # Automatically creates tag
        incident_pk = self.add_incident()
        tag = str(Tag.objects.first())
        response = self.client.delete(path=f"/api/v1/incidents/{incident_pk}/tags/{tag}/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Tag.objects.count(), 0)

    def test_putting_ticket_url_creates_ticket_url(self):
        incident_pk = self.add_incident()
        data = {
            "ticket_url": "www.example.com",
        }
        response = self.client.put(path=f"/api/v1/incidents/{incident_pk}/ticket_url/", data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ticket_url"], data["ticket_url"])
        self.assertEqual(Incident.objects.get(id=incident_pk).ticket_url, data["ticket_url"])

    def test_get_my_incidents_returns_my_incidents(self):
        incident_pk = self.add_incident()
        response = self.client.get(path="/api/v1/incidents/mine/")
        self.assertTrue(Incident.objects.exists())
        self.assertEqual(response.status_code, 200)
        # Paging, so check "results"
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_posting_incident_to_mine_with_tag_should_create_incident_and_tag(self):
        # Start with no incidents or tags
        self.assertFalse(Incident.objects.exists())
        self.assertFalse(Tag.objects.exists())
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v1/incidents/mine/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        # Check that we have made the correct Incident
        self.assertEqual(response.data["description"], data["description"])
        self.assertTrue(Incident.objects.exists())
        obj = Incident.objects.get()
        self.assertEqual(obj.description, data["description"])
        # Check that we have made the correct Tag
        self.assertTrue(Tag.objects.exists())
        tag = Tag.objects.get()
        self.assertEqual(obj.tags, [tag])
        self.assertEqual(str(tag), data["tags"][0]["tag"])

    def test_incident_source_types_returns_correct_source_types(self):
        response = self.client.get(path=f"/api/v1/incidents/source-types/")
        self.assertEqual(response.status_code, 200)
        source_types = set([type.name for type in SourceSystemType.objects.all()])
        response_types = set([type["name"] for type in response.data])
        self.assertEqual(response_types, source_types)

    def test_posting_source_type_creates_source_type(self):
        data = {
            "name": "test",
        }
        response = self.client.post(path=f"/api/v1/incidents/source-types/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["name"], data["name"])
        self.assertTrue(SourceSystemType.objects.filter(name=data["name"]).exists())

    def test_get_source_type_by_name_returns_correct_source_type(self):
        response = self.client.get(path=f"/api/v1/incidents/source-types/{self.source.type.name}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], self.source.type.name)

    def test_incident_sources_returns_correct_sources(self):
        response = self.client.get(path=f"/api/v1/incidents/sources/")
        self.assertEqual(response.status_code, 200)
        source_pks = set([source.pk for source in SourceSystem.objects.all()])
        response_source_pks = set([source["pk"] for source in response.data])
        self.assertEqual(response_source_pks, source_pks)

    def test_posting_source_creates_source(self):
        # Only admins can create sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newtest",
            "type": self.source.type.name,
        }
        response = self.client.post(path=f"/api/v1/incidents/sources/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["name"], data["name"])
        self.assertTrue(SourceSystem.objects.filter(name=data["name"]).exists())

    def test_get_source_by_pk_returns_correct_source(self):
        response = self.client.get(path=f"/api/v1/incidents/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pk"], self.source.pk)

    def test_update_source(self):
        # Only admins can update sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newname",
        }
        response = self.client.put(path=f"/api/v1/incidents/sources/{self.source.pk}/", data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], data["name"])


class IncidentViewSetTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        disconnect_signals()
        source_type = SourceSystemTypeFactory()
        cls.user = SourceUserFactory()
        cls.source = SourceSystemFactory(type=source_type, user=cls.user)
        cls.admin = AdminUserFactory()

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    @classmethod
    def tearDownClass(cls):
        connect_signals()

    def add_incident(self, description="incident"):
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": description,
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v2/incidents/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        return response.data["pk"]

    def add_acknowledgement(self, incident_pk, description="acknowledgement"):
        data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "type": "STA",
                "description": description,
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/acks/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        return response.data["pk"]

    def add_event(self, incident_pk, description="event"):
        data = {
            "timestamp": "2022-08-02T13:04:03.529Z",
            "type": "OTH",
            "description": description,
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident_pk}/events/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        return response.data["pk"]

    def test_no_incidents_returns_empty_list(self):
        response = self.client.get(path="/api/v2/incidents/")
        self.assertFalse(Incident.objects.exists())
        self.assertEqual(response.status_code, 200)
        # Paging, so check "results"
        self.assertEqual(response.data["results"], [])

    def test_get_incident_returns_all_incidents(self):
        incident_pk = self.add_incident()
        response = self.client.get(path="/api/v2/incidents/")
        self.assertTrue(Incident.objects.exists())
        self.assertEqual(response.status_code, 200)
        # Paging, so check "results"
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_incident_search_existing_incident_description(self):
        pk = self.add_incident(description="incident1")
        response = self.client.get(path="/api/v2/incidents/?search=incident1")
        self.assertEqual(response.data["results"][0]["pk"], pk)

    def test_incident_search_existing_event_description(self):
        incident_pk = self.add_incident(description="incident1")
        self.add_event(incident_pk=incident_pk, description="event1")
        response = self.client.get(path="/api/v2/incidents/?search=event1")
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_incident_search_nonexisting_description(self):
        incident_pk = self.add_incident(description="incident1")
        self.add_event(incident_pk=incident_pk, description="event1")
        response = self.client.get(path="/api/v2/incidents/?search=not_a_description")
        self.assertEqual(response.data["results"], [])

    def test_incident_search_existing_descriptions(self):
        incident_pk = self.add_incident(description="incident1")
        self.add_event(incident_pk=incident_pk, description="event")
        self.add_incident(description="incident2")
        self.add_event(incident_pk=incident_pk, description="event")
        response = self.client.get(path="/api/v2/incidents/?search=incident1,event")
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_incident_search_multiple_incidents(self):
        incident_pk1 = self.add_incident(description="incident1")
        incident_pk2 = self.add_incident(description="incident2")
        self.add_event(incident_pk=incident_pk1, description="event1")
        self.add_event(incident_pk=incident_pk2, description="event2")
        response = self.client.get(path="/api/v2/incidents/?search=incident")
        self.assertEqual(len(response.data["results"]), 2)

    def test_incident_search_incident_and_event(self):
        incident_pk1 = self.add_incident(description="target_incident")
        incident_pk2 = self.add_incident(description="incident2")
        self.add_event(incident_pk=incident_pk1, description="event1")
        self.add_event(incident_pk=incident_pk2, description="target_event")
        response = self.client.get(path="/api/v2/incidents/?search=target")
        self.assertEqual(len(response.data["results"]), 2)

    def test_posting_incident_with_tag_should_create_incident_and_tag(self):
        # Start with no incidents or tags
        self.assertFalse(Incident.objects.exists())
        self.assertFalse(Tag.objects.exists())
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v2/incidents/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        # Check that we have made the correct Incident
        self.assertEqual(response.data["description"], data["description"])
        self.assertTrue(Incident.objects.exists())
        obj = Incident.objects.get()
        self.assertEqual(obj.description, data["description"])
        # Check that we have made the correct Tag
        self.assertTrue(Tag.objects.exists())
        tag = Tag.objects.get()
        self.assertEqual(obj.tags, [tag])
        self.assertEqual(str(tag), data["tags"][0]["tag"])

    def test_get_incident_by_pk_returns_correct_incident(self):
        incident_pk = self.add_incident()
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pk"], incident_pk)

    def test_incident_can_properly_change_level(self):
        incident_pk = self.add_incident()
        incident_path = reverse("v2:incident:incident-detail", args=[incident_pk])
        response = self.client.put(
            path=incident_path,
            data={
                "tags": [{"tag": "a=b"}],
                "level": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(pk=incident_pk).level, 2)

    def test_incident_acks_returns_correct_acks(self):
        incident_pk = self.add_incident()
        ack_pk = self.add_acknowledgement(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/acks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["event"]["pk"], ack_pk)
        self.assertEqual(response.data[0]["event"]["type"]["value"], "ACK")

    def test_posting_acknowledgement_creates_acknowledgement(self):
        incident_pk = self.add_incident()
        self.assertFalse(Acknowledgement.objects.exists())
        data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "type": "STA",
                "description": "acknowledgement",
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident_pk}/acks/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")
        self.assertEqual(response.data["event"]["description"], data["event"]["description"])

    def test_get_acknowledgement_by_pk_returns_correct_acknowledgement(self):
        incident_pk = self.add_incident()
        ack_pk = self.add_acknowledgement(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/acks/{ack_pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["event"]["pk"], ack_pk)
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")

    def test_incident_events_returns_correct_events_of_incident(self):
        incident_pk = self.add_incident()
        event_pk = self.add_event(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["pk"], event_pk)
        self.assertEqual(response.data[0]["type"]["value"], "OTH")

    def test_posting_event_creates_event(self):
        incident_pk = self.add_incident()
        self.assertFalse(Acknowledgement.objects.exists())
        data = {
            "timestamp": "2022-08-02T13:45:44.056Z",
            "type": "OTH",
            "description": "event",
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident_pk}/events/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["type"]["value"], "OTH")
        self.assertEqual(response.data["description"], data["description"])

    def test_get_event_by_pk_returns_correct_event(self):
        incident_pk = self.add_incident()
        event_pk = self.add_event(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/events/{event_pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pk"], event_pk)
        self.assertEqual(response.data["type"]["value"], "OTH")

    def test_incident_tags_returns_correct_tags(self):
        # Automatically creates tag
        incident_pk = self.add_incident()
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/tags/")
        tag = str(Tag.objects.first())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["tag"], tag)

    def test_posting_tag_creates_tag(self):
        # Automatically creates tag
        incident_pk = self.add_incident()
        self.assertEqual(Tag.objects.count(), 1)
        data = {
            "tag": "c=d",
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident_pk}/tags/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["tag"], data["tag"])
        self.assertEqual(Tag.objects.count(), 2)

    def test_get_tag_by_tag_returns_correct_tag(self):
        # Automatically creates tag
        incident_pk = self.add_incident()
        tag = str(Tag.objects.first())
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/tags/{tag}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tag"], tag)

    def test_delete_tag_deletes_tag(self):
        # Automatically creates tag
        incident_pk = self.add_incident()
        tag = str(Tag.objects.first())
        response = self.client.delete(path=f"/api/v2/incidents/{incident_pk}/tags/{tag}/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Tag.objects.count(), 0)

    def test_putting_ticket_url_creates_ticket_url(self):
        incident_pk = self.add_incident()
        data = {
            "ticket_url": "www.example.com",
        }
        response = self.client.put(path=f"/api/v2/incidents/{incident_pk}/ticket_url/", data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ticket_url"], data["ticket_url"])
        self.assertEqual(Incident.objects.get(id=incident_pk).ticket_url, data["ticket_url"])

    def test_incident_events_returns_correct_events(self):
        incident_pk = self.add_incident()
        event_pk = self.add_event(incident_pk=incident_pk)
        response = self.client.get(path=f"/api/v2/incidents/events/")
        self.assertEqual(response.status_code, 200)
        # Paging, so check "results"
        self.assertEqual(response.data["results"][0]["pk"], event_pk)
        self.assertEqual(response.data["results"][0]["type"]["value"], "OTH")

    def test_incident_source_types_returns_correct_source_types(self):
        response = self.client.get(path=f"/api/v2/incidents/source-types/")
        self.assertEqual(response.status_code, 200)
        source_types = set([type.name for type in SourceSystemType.objects.all()])
        response_types = set([type["name"] for type in response.data])
        self.assertEqual(response_types, source_types)

    def test_posting_source_type_creates_source_type(self):
        data = {
            "name": "test",
        }
        response = self.client.post(path=f"/api/v2/incidents/source-types/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["name"], data["name"])
        self.assertTrue(SourceSystemType.objects.filter(name=data["name"]).exists())

    def test_get_source_type_by_name_returns_correct_source_type(self):
        response = self.client.get(path=f"/api/v2/incidents/source-types/{self.source.type.name}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], self.source.type.name)

    def test_incident_sources_returns_correct_sources(self):
        response = self.client.get(path=f"/api/v2/incidents/sources/")
        self.assertEqual(response.status_code, 200)
        source_pks = set([source.pk for source in SourceSystem.objects.all()])
        response_source_pks = set([source["pk"] for source in response.data])
        self.assertEqual(response_source_pks, source_pks)

    def test_posting_source_creates_source(self):
        # Only admins can create sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newtest",
            "type": self.source.type.name,
        }
        response = self.client.post(path=f"/api/v2/incidents/sources/", data=data, format="json")
        self.assertEqual(response.status_code, 201)  # Created
        self.assertEqual(response.data["name"], data["name"])
        self.assertTrue(SourceSystem.objects.filter(name=data["name"]).exists())

    def test_get_source_by_pk_returns_correct_source(self):
        response = self.client.get(path=f"/api/v2/incidents/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pk"], self.source.pk)

    def test_update_source(self):
        # Only admins can update sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newname",
        }
        response = self.client.put(path=f"/api/v2/incidents/sources/{self.source.pk}/", data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], data["name"])
