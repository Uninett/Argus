from django.urls import reverse
from django.test import TestCase, RequestFactory

from rest_framework import serializers, status, versioning
from rest_framework.test import APITestCase

from argus.auth.factories import SourceUserFactory
from argus.incident.factories import (
    SourceSystemTypeFactory,
    SourceSystemFactory,
    StatefulIncidentFactory,
    StatelessIncidentFactory,
)
from argus.incident.models import Event, Incident, Tag
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
        request = viewfactory.get(f"/api/v1/incidents/{incident.pk}/events/")
        request.versioning_scheme = versioning.NamespaceVersioning()
        request.version = "v1"
        view = EventViewSet()
        view.request = request
        with self.assertRaises(serializers.ValidationError):
            view.validate_event_type_for_incident(Event.Type.ACKNOWLEDGE, incident)


class IncidentAPITestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        disconnect_signals()
        source_type = SourceSystemTypeFactory()
        cls.user = SourceUserFactory()
        cls.source = SourceSystemFactory(type=source_type, user=cls.user)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    @classmethod
    def tearDownClass(cls):
        connect_signals()


class IncidentViewSetV1TestCase(IncidentAPITestCase):
    def add_closed_incident(self, description="closed_incident"):
        return StatefulIncidentFactory(
            description=description, start_time="2022-05-23T13:07:29.254Z", end_time="2022-05-24T13:07:29.254Z"
        ).pk

    def test_no_incidents_returns_empty_list(self):
        response = self.client.get("/api/v1/incidents/")
        self.assertFalse(Incident.objects.exists())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        self.assertEqual(response.data["results"], [])

    def test_posting_incident_with_tag_should_create_incident_and_tag(self):
        # Start with no incidents or tags
        self.assertFalse(Incident.objects.exists())
        self.assertFalse(Tag.objects.exists())
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "string",
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post("/api/v1/incidents/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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

    def test_incident_can_properly_change_level(self):
        incident_pk = self.add_closed_incident("incident1")
        incident_path = reverse("v1:incident:incident-detail", args=[incident_pk])
        response = self.client.put(
            incident_path,
            {
                "tags": [{"tag": "a=b"}],
                "level": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(pk=incident_pk).level, 2)


class IncidentFilterByOpenAndStatefulV1TestCase(IncidentAPITestCase):
    def setUp(self):
        super().setUp()
        self.open_pk = StatefulIncidentFactory().pk
        self.closed_pk = StatefulIncidentFactory(
            start_time="2022-05-23T13:07:29.254Z", end_time="2022-05-24T13:07:29.254Z"
        ).pk
        self.stateless_pk = StatelessIncidentFactory().pk

    def test_open_true_returns_only_open_incidents(self):
        response = self.client.get("/api/v1/incidents/?open=true")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], self.open_pk)

    def test_open_false_returns_only_closed_incidents(self):
        response = self.client.get("/api/v1/incidents/?open=false")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], self.closed_pk)

    def test_stateful_false_returns_only_stateless_incidents(self):
        response = self.client.get("/api/v1/incidents/?stateful=false")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], self.stateless_pk)

    def test_stateful_true_returns_only_stateful_incidents(self):
        response = self.client.get("/api/v1/incidents/?stateful=true")
        self.assertEqual(len(response.data["results"]), 2)
        response_pks = set([result["pk"] for result in response.data["results"]])
        self.assertEqual(response_pks, set([self.open_pk, self.closed_pk]))

    def test_open_true_and_stateful_true_returns_only_open_incidents(self):
        response = self.client.get("/api/v1/incidents/?open=true&stateful=true")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], self.open_pk)

    def test_open_true_and_stateful_false_returns_no_incidents(self):
        response = self.client.get("/api/v1/incidents/?stateful=false&open=true")
        self.assertEqual(len(response.data["results"]), 0, msg=response.data)

    def test_open_false_and_stateful_true_returns_only_closed_incidents(self):
        response = self.client.get("/api/v1/incidents/?open=false&stateful=true")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], self.closed_pk)

    def test_open_false_and_stateful_false_returns_no_incidents(self):
        response = self.client.get("/api/v1/incidents/?stateful=false&open=false")
        self.assertEqual(len(response.data["results"]), 0, msg=response.data)


class IncidentViewSetTestCase(IncidentAPITestCase):
    def add_incident(self, description="incident"):
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": description,
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post("/api/v2/incidents/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["pk"]

    def add_event(self, incident_pk, description="event"):
        event_data = {"timestamp": "2021-08-04T09:14:55.908Z", "type": "OTH", "description": description}
        response = self.client.post(f"/api/v2/incidents/{incident_pk}/events/", event_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_incident_search_existing_incident_description(self):
        pk = self.add_incident("incident1")
        response = self.client.get("/api/v2/incidents/?search=incident1")
        self.assertEqual(response.data["results"][0]["pk"], pk)

    def test_incident_search_existing_event_description(self):
        pk = self.add_incident("incident1")
        self.add_event(pk, "event1")
        response = self.client.get("/api/v2/incidents/?search=event1")
        self.assertEqual(response.data["results"][0]["pk"], pk)

    def test_incident_search_nonexisting_description(self):
        pk = self.add_incident("incident1")
        self.add_event(pk, "event1")
        response = self.client.get("/api/v2/incidents/?search=not_a_description")
        self.assertEqual(response.data["results"], [])

    def test_incident_search_existing_descriptions(self):
        pk = self.add_incident("incident1")
        self.add_event(pk, "event")
        pk2 = self.add_incident("incident2")
        self.add_event(pk2, "event")
        response = self.client.get("/api/v2/incidents/?search=incident1,event")
        self.assertEqual(response.data["results"][0]["pk"], pk)

    def test_incident_search_multiple_incidents(self):
        pk1 = self.add_incident("incident1")
        pk2 = self.add_incident("incident2")
        self.add_event(pk1, "event1")
        self.add_event(pk2, "event2")
        response = self.client.get("/api/v2/incidents/?search=incident")
        self.assertEqual(len(response.data["results"]), 2)

    def test_incident_search_incident_and_event(self):
        pk1 = self.add_incident("target_incident")
        pk2 = self.add_incident("incident2")
        self.add_event(pk1, "event1")
        self.add_event(pk2, "target_event")
        response = self.client.get("/api/v2/incidents/?search=target")
        self.assertEqual(len(response.data["results"]), 2)
