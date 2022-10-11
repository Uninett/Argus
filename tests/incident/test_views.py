import datetime
import pytz

from django.conf import settings
from django.urls import reverse
from django.test import TestCase, RequestFactory

from rest_framework import serializers, status, versioning
from rest_framework.test import APITestCase

from argus.auth.factories import AdminUserFactory, SourceUserFactory
from argus.incident.factories import (
    AcknowledgementFactory,
    EventFactory,
    IncidentTagRelationFactory,
    SourceSystemTypeFactory,
    SourceSystemFactory,
    StatefulIncidentFactory,
    StatelessIncidentFactory,
    TagFactory,
)
from argus.incident.models import (
    Acknowledgement,
    Event,
    Incident,
    IncidentTagRelation,
    SourceSystem,
    SourceSystemType,
    Tag,
)
from argus.incident.views import EventViewSet
from argus.util.testing import disconnect_signals, connect_signals

TIME_ZONE = getattr(settings, "TIME_ZONE")


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
    def setUp(self):
        disconnect_signals()
        source_type = SourceSystemTypeFactory()
        self.user = SourceUserFactory()
        self.source = SourceSystemFactory(type=source_type, user=self.user)
        self.admin = AdminUserFactory()
        self.client.force_authenticate(user=self.user)

    def teardown(self):
        connect_signals()


class IncidentViewSetV1TestCase(IncidentAPITestCase):
    def add_open_incident_with_start_event_and_tag(self, description="incident"):
        incident = StatefulIncidentFactory(source=self.source, description=description)
        tag = TagFactory(key="a", value="b")
        IncidentTagRelationFactory(incident=incident, tag=tag)
        return incident

    def add_acknowledgement_with_incident_and_event(self):
        return AcknowledgementFactory()

    def test_no_incidents_returns_empty_list(self):
        response = self.client.get("/api/v1/incidents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        self.assertEqual(response.data["results"], [])

    def test_can_get_all_incidents(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path="/api/v1/incidents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_can_get_specific_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], incident_pk)

    def test_can_create_incident_with_tag(self):
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v1/incidents/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that we have made the correct Incident
        self.assertEqual(response.data["description"], data["description"])
        incident = Incident.objects.get()
        incident_tags = [relation.tag for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertEqual(incident.description, data["description"])
        # Check that we have made the correct Tag
        tag = Tag.objects.get()
        self.assertEqual(incident_tags, [tag])
        self.assertEqual(str(tag), data["tags"][0]["tag"])

    def test_can_update_incident_level(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
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

    def test_can_get_all_acknowledgements_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident_pk = ack.event.incident.pk
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/acks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], ack.pk)
        self.assertEqual(response.data[0]["event"]["type"]["value"], "ACK")

    def test_can_get_specific_acknowledgement_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident_pk = ack.event.incident.pk
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/acks/{ack.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["event"]["pk"], ack.pk)
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")

    def test_can_create_acknowledgement_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "type": "STA",
                "description": "acknowledgement",
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/acks/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")
        self.assertEqual(response.data["event"]["description"], data["event"]["description"])

    def test_can_update_acknowledgement_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident_pk = ack.event.incident.pk
        data = {
            "expiration": (datetime.datetime.now(tz=pytz.timezone(TIME_ZONE)) + datetime.timedelta(days=3)).isoformat(),
        }
        response = self.client.put(path=f"/api/v1/incidents/{incident_pk}/acks/{ack.pk}/", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["expiration"], data["expiration"])

    def test_can_get_all_events_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        event_pk = Event.objects.get(incident_id=incident_pk).pk
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], event_pk)

    def test_can_get_specific_event_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        event_pk = Event.objects.get(incident_id=incident_pk).pk
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/events/{event_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], event_pk)

    def test_can_create_event_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        self.assertEqual(Event.objects.count(), 1)
        data = {
            "timestamp": "2022-08-02T13:45:44.056Z",
            "type": "OTH",
            "description": "event",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/events/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["type"]["value"], "OTH")
        self.assertEqual(response.data["description"], data["description"])
        self.assertEqual(Event.objects.count(), 2)

    def test_can_get_all_tags_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/tags/")
        tag = str(Tag.objects.get())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["tag"], tag)

    def test_can_get_specific_tag_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        tag = str(Tag.objects.get())
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/tags/{tag}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tag"], tag)

    def test_can_create_tag_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        self.assertEqual(Tag.objects.count(), 1)
        data = {
            "tag": "c=d",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident_pk}/tags/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tag"], data["tag"])
        self.assertEqual(Tag.objects.count(), 2)

    def test_can_delete_tag_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        tag = str(Tag.objects.get())
        response = self.client.delete(path=f"/api/v1/incidents/{incident_pk}/tags/{tag}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Tag.objects.count(), 0)

    def test_can_create_ticket_url_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        data = {
            "ticket_url": "www.example.com",
        }
        response = self.client.put(path=f"/api/v1/incidents/{incident_pk}/ticket_url/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ticket_url"], data["ticket_url"])
        self.assertEqual(Incident.objects.get(id=incident_pk).ticket_url, data["ticket_url"])

    def test_can_get_my_incidents(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path="/api/v1/incidents/mine/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_can_create_my_incident_with_tag(self):
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v1/incidents/mine/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that we have made the correct Incident
        self.assertEqual(response.data["description"], data["description"])
        incident = Incident.objects.get()
        incident_tags = [relation.tag for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertEqual(incident.description, data["description"])
        # Check that we have made the correct Tag
        tag = Tag.objects.get()
        self.assertEqual(incident_tags, [tag])
        self.assertEqual(str(tag), data["tags"][0]["tag"])

    def test_can_get_all_source_types(self):
        response = self.client.get(path=f"/api/v1/incidents/source-types/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        source_types = set([type.name for type in SourceSystemType.objects.all()])
        response_types = set([type["name"] for type in response.data])
        self.assertEqual(response_types, source_types)

    def test_can_get_specific_source_type(self):
        response = self.client.get(path=f"/api/v1/incidents/source-types/{self.source.type.name}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.source.type.name)

    def test_can_create_source_type(self):
        # One source system type is created on setup
        self.assertEqual(SourceSystemType.objects.count(), 1)
        data = {
            "name": "test",
        }
        response = self.client.post(path=f"/api/v1/incidents/source-types/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], data["name"])
        self.assertEqual(SourceSystemType.objects.count(), 2)
        self.assertTrue(SourceSystemType.objects.filter(name=data["name"]).exists())

    def test_can_get_all_source_systems(self):
        response = self.client.get(path=f"/api/v1/incidents/sources/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        source_pks = set([source.pk for source in SourceSystem.objects.all()])
        response_source_pks = set([source["pk"] for source in response.data])
        self.assertEqual(response_source_pks, source_pks)

    def test_can_get_specific_source_system(self):
        response = self.client.get(path=f"/api/v1/incidents/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], self.source.pk)

    def test_can_create_source_system(self):
        # Only admins can create sources
        self.client.force_authenticate(user=self.admin)
        # One source system is created on setup
        self.assertEqual(SourceSystem.objects.count(), 1)
        data = {
            "name": "newtest",
            "type": self.source.type.name,
        }
        response = self.client.post(path=f"/api/v1/incidents/sources/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], data["name"])
        self.assertEqual(SourceSystem.objects.count(), 2)
        self.assertTrue(SourceSystem.objects.filter(name=data["name"]).exists())

    def test_can_update_source_system(self):
        # Only admins can update sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newname",
        }
        response = self.client.put(path=f"/api/v1/incidents/sources/{self.source.pk}/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], data["name"])


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


class IncidentViewSetTestCase(APITestCase):
    def setUp(self):
        disconnect_signals()
        source_type = SourceSystemTypeFactory()
        self.user = SourceUserFactory()
        self.source = SourceSystemFactory(type=source_type, user=self.user)
        self.admin = AdminUserFactory()
        self.client.force_authenticate(user=self.user)

    def teardown(self):
        connect_signals()

    def add_open_incident_with_start_event_and_tag(self, description="incident"):
        incident = StatefulIncidentFactory(source=self.source, description=description)
        tag = TagFactory(key="a", value="b")
        IncidentTagRelationFactory(incident=incident, tag=tag)
        return incident

    def add_event(self, incident_pk, description="event", type=Event.Type.OTHER):
        return EventFactory(incident_id=incident_pk, description=description, type=type)

    def add_acknowledgement_with_incident_and_event(self):
        return AcknowledgementFactory()

    def test_can_get_all_incidents(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path="/api/v2/incidents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_can_get_incident_by_incident_description(self):
        pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        response = self.client.get(path="/api/v2/incidents/?search=incident1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], pk)

    def test_can_get_incident_by_event_description(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        self.add_event(incident_pk=incident_pk, description="event1")
        response = self.client.get(path="/api/v2/incidents/?search=event1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_cannot_get_incident_by_nonexisting_description(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        self.add_event(incident_pk=incident_pk, description="event1")
        response = self.client.get(path="/api/v2/incidents/?search=not_a_description")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)
        self.assertEqual(response.data["results"], [])

    def test_can_get_incident_by_incident_description_and_event_description(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        self.add_event(incident_pk=incident_pk, description="event")
        self.add_open_incident_with_start_event_and_tag(description="incident2")
        self.add_event(incident_pk=incident_pk, description="event")
        response = self.client.get(path="/api/v2/incidents/?search=incident1,event")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_can_get_multiple_incidents_by_incident_description(self):
        incident_pk1 = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        incident_pk2 = self.add_open_incident_with_start_event_and_tag(description="incident2").pk
        self.add_event(incident_pk=incident_pk1, description="event1")
        self.add_event(incident_pk=incident_pk2, description="event2")
        response = self.client.get(path="/api/v2/incidents/?search=incident")
        response_pks = set([incident["pk"] for incident in response.data["results"]])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response_pks, set([incident_pk1, incident_pk2]))

    def test_can_get_multiple_incidents_by_incident_description_and_event_description(self):
        incident_pk1 = self.add_open_incident_with_start_event_and_tag(description="target_incident").pk
        incident_pk2 = self.add_open_incident_with_start_event_and_tag(description="incident2").pk
        self.add_event(incident_pk=incident_pk1, description="event1")
        self.add_event(incident_pk=incident_pk2, description="target_event")
        response = self.client.get(path="/api/v2/incidents/?search=target")
        response_pks = set([incident["pk"] for incident in response.data["results"]])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response_pks, set([incident_pk1, incident_pk2]))

    def test_can_get_specific_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], incident_pk)

    def test_can_create_incident_with_tag(self):
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v2/incidents/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that we have made the correct Incident
        self.assertEqual(response.data["description"], data["description"])
        incident = Incident.objects.get()
        incident_tags = [relation.tag for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertEqual(incident.description, data["description"])
        # Check that we have made the correct Tag
        tag = Tag.objects.get()
        self.assertEqual(incident_tags, [tag])
        self.assertEqual(str(tag), data["tags"][0]["tag"])

    def test_can_update_incident_level(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
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

    def test_can_get_all_acknowledgements_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident_pk = ack.event.incident.pk
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/acks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], ack.pk)
        self.assertEqual(response.data[0]["event"]["type"]["value"], "ACK")

    def test_can_get_specific_acknowledgement_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident_pk = ack.event.incident.pk
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/acks/{ack.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["event"]["pk"], ack.pk)
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")

    def test_can_create_acknowledgement_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "type": "STA",
                "description": "acknowledgement",
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident_pk}/acks/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")
        self.assertEqual(response.data["event"]["description"], data["event"]["description"])

    def test_can_update_acknowledgement_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident_pk = ack.event.incident.pk
        data = {
            "expiration": (datetime.datetime.now(tz=pytz.timezone(TIME_ZONE)) + datetime.timedelta(days=3)).isoformat(),
        }
        response = self.client.put(path=f"/api/v2/incidents/{incident_pk}/acks/{ack.pk}/", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["expiration"], data["expiration"])

    def test_can_get_all_events_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        event_pk = Event.objects.get(incident_id=incident_pk).pk
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], event_pk)

    def test_can_get_specific_event_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        event_pk = incident.events.get().pk
        response = self.client.get(path=f"/api/v2/incidents/{incident.pk}/events/{event_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], event_pk)

    def test_can_create_event_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        self.assertEqual(Event.objects.count(), 1)
        data = {
            "timestamp": "2022-08-02T13:45:44.056Z",
            "type": "OTH",
            "description": "event",
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident_pk}/events/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["type"]["value"], "OTH")
        self.assertEqual(response.data["description"], data["description"])
        self.assertEqual(Event.objects.count(), 2)

    def test_can_get_all_tags_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/tags/")
        tag = str(Tag.objects.get())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["tag"], tag)

    def test_can_get_specific_tag_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        tag = str(Tag.objects.get())
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/tags/{tag}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tag"], tag)

    def test_can_create_tag_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        self.assertEqual(Tag.objects.count(), 1)
        data = {
            "tag": "c=d",
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident_pk}/tags/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tag"], data["tag"])
        self.assertEqual(Tag.objects.count(), 2)

    def test_can_delete_tag_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        tag = str(Tag.objects.get())
        response = self.client.delete(path=f"/api/v2/incidents/{incident_pk}/tags/{tag}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_can_create_ticket_url_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        data = {
            "ticket_url": "www.example.com",
        }
        response = self.client.put(path=f"/api/v2/incidents/{incident_pk}/ticket_url/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ticket_url"], data["ticket_url"])
        self.assertEqual(Incident.objects.get(id=incident_pk).ticket_url, data["ticket_url"])

    def test_can_get_my_incidents(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path="/api/v2/incidents/mine/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_can_create_my_incident_with_tag(self):
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": [{"tag": "a=b"}],
        }
        response = self.client.post(path="/api/v2/incidents/mine/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that we have made the correct Incident
        self.assertEqual(response.data["description"], data["description"])
        incident = Incident.objects.get()
        incident_tags = [relation.tag for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertEqual(incident.description, data["description"])
        # Check that we have made the correct Tag
        tag = Tag.objects.get()
        self.assertEqual(incident_tags, [tag])
        self.assertEqual(str(tag), data["tags"][0]["tag"])

    def test_can_get_all_events(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        event_pk = incident.events.get().pk
        response = self.client.get(path=f"/api/v2/incidents/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["pk"], event_pk)

    def test_can_get_all_source_types(self):
        response = self.client.get(path=f"/api/v2/incidents/source-types/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        source_types = set([type.name for type in SourceSystemType.objects.all()])
        response_types = set([type["name"] for type in response.data])
        self.assertEqual(response_types, source_types)

    def test_can_get_specific_source_type(self):
        response = self.client.get(path=f"/api/v2/incidents/source-types/{self.source.type.name}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.source.type.name)

    def test_can_create_source_type(self):
        # One source system type is created on setup
        self.assertEqual(SourceSystemType.objects.count(), 1)
        data = {
            "name": "test",
        }
        response = self.client.post(path=f"/api/v2/incidents/source-types/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], data["name"])
        self.assertEqual(SourceSystemType.objects.count(), 2)
        self.assertTrue(SourceSystemType.objects.filter(name=data["name"]).exists())

    def test_can_get_all_source_systems(self):
        response = self.client.get(path=f"/api/v2/incidents/sources/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        source_pks = set([source.pk for source in SourceSystem.objects.all()])
        response_source_pks = set([source["pk"] for source in response.data])
        self.assertEqual(response_source_pks, source_pks)

    def test_can_get_specific_source_system(self):
        response = self.client.get(path=f"/api/v2/incidents/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], self.source.pk)

    def test_can_create_source_system(self):
        # Only admins can create sources
        self.client.force_authenticate(user=self.admin)
        # One source system is created on setup
        self.assertEqual(SourceSystem.objects.count(), 1)
        data = {
            "name": "newtest",
            "type": self.source.type.name,
        }
        response = self.client.post(path=f"/api/v2/incidents/sources/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], data["name"])
        self.assertEqual(SourceSystem.objects.count(), 2)
        self.assertTrue(SourceSystem.objects.filter(name=data["name"]).exists())

    def test_can_update_source_system(self):
        # Only admins can update sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newname",
        }
        response = self.client.put(path=f"/api/v2/incidents/sources/{self.source.pk}/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], data["name"])
