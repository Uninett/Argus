from django.test import TestCase, RequestFactory

from rest_framework import serializers, versioning
from rest_framework.test import APITestCase

from argus.auth.factories import SourceUserFactory
from argus.incident.factories import SourceSystemTypeFactory, SourceSystemFactory, StatefulIncidentFactory
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


class IncidentViewSetV1TestCase(APITestCase):
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

    def test_no_incidents_returns_empty_list(self):
        response = self.client.get("/api/v1/incidents/")
        self.assertFalse(Incident.objects.exists())
        self.assertEqual(response.status_code, 200)
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
