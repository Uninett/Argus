import datetime

from django.urls import reverse
from django.utils.timezone import now
from django.test import TestCase, RequestFactory

from rest_framework import serializers, status, versioning
from rest_framework.test import APITestCase

from argus.auth.factories import AdminUserFactory, BaseUserFactory, SourceUserFactory
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
        self.add_open_incident_with_start_event_and_tag()
        incident_pks = list(Incident.objects.all().values_list("pk", flat=True))

        response = self.client.get(path="/api/v1/incidents/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        response_pks = [incident["pk"] for incident in response.data["results"]]
        self.assertEqual(response_pks, incident_pks)

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
        self.assertTrue(Incident.objects.filter(id=response.data["pk"]).exists())
        incident = Incident.objects.get(id=response.data["pk"])
        # Check that we have made the correct Tag
        tag = data["tags"][0]["tag"]
        key, value = Tag.split(tag)
        self.assertTrue(Tag.objects.filter(key=key, value=value).exists())
        tag = Tag.objects.get(key=key, value=value)
        # Check that incident and tag are linked
        self.assertTrue(IncidentTagRelation.objects.filter(incident=incident).filter(tag=tag).exists())

    def test_can_update_incident_level(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        incident_path = reverse("v1:incident:incident-detail", args=[incident_pk])
        response = self.client.patch(
            path=incident_path,
            data={
                "level": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(pk=incident_pk).level, 2)

    def test_can_get_all_acknowledgements_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident = ack.event.incident
        ack_pks = list(incident.acks.all().values_list("pk", flat=True))

        response = self.client.get(path=f"/api/v1/incidents/{incident.pk}/acks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_pks = [ack["pk"] for ack in response.data]
        self.assertEqual(response_pks, ack_pks)
        event_types = [ack["event"]["type"]["value"] for ack in response.data]
        self.assertEqual(set(event_types), {"ACK"})

    def test_can_get_specific_acknowledgement_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident_pk = ack.event.incident.pk
        response = self.client.get(path=f"/api/v1/incidents/{incident_pk}/acks/{ack.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["event"]["pk"], ack.pk)
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")

    def test_can_create_acknowledgement_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "type": "STA",
                "description": "acknowledgement",
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident.pk}/acks/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(incident.events.filter(id=response.data["pk"]).exists())
        self.assertTrue(Acknowledgement.objects.filter(event_id=response.data["pk"]).exists())

    def test_can_update_acknowledgement_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident = ack.event.incident
        data = {
            "expiration": (now() + datetime.timedelta(days=3)).isoformat(),
        }
        response = self.client.put(path=f"/api/v1/incidents/{incident.pk}/acks/{ack.pk}/", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            incident.events.get(pk=ack.pk).ack.expiration, datetime.datetime.fromisoformat(data["expiration"])
        )

    def test_can_get_all_events_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        event_pks = list(incident.events.all().values_list("pk", flat=True))

        response = self.client.get(path=f"/api/v1/incidents/{incident.pk}/events/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_pks = [ack["pk"] for ack in response.data]
        self.assertEqual(response_pks, event_pks)

    def test_can_get_specific_event_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        event_pk = incident.events.first().pk
        response = self.client.get(path=f"/api/v1/incidents/{incident.pk}/events/{event_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], event_pk)

    def test_can_create_event_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = {
            "timestamp": "2022-08-02T13:45:44.056Z",
            "type": "OTH",
            "description": "event",
        }
        response = self.client.post(path=f"/api/v1/incidents/{incident.pk}/events/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(incident.events.filter(id=response.data["pk"]).exists())

    def test_can_get_all_tags_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tags = [str(relation.tag) for relation in incident.incident_tag_relations.all()]

        response = self.client.get(path=f"/api/v1/incidents/{incident.pk}/tags/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_tags = [tag["tag"] for tag in response.data]
        self.assertEqual(response_tags, tags)

    def test_can_get_specific_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tag = incident.incident_tag_relations.first().tag
        response = self.client.get(path=f"/api/v1/incidents/{incident.pk}/tags/{tag}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tag"], str(tag))

    def test_can_create_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = {
            "tag": "c=d",
        }

        response = self.client.post(path=f"/api/v1/incidents/{incident.pk}/tags/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        incident_tags = [str(relation.tag) for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertIn(data["tag"], incident_tags)

    def test_can_delete_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tag = incident.incident_tag_relations.first().tag

        response = self.client.delete(path=f"/api/v1/incidents/{incident.pk}/tags/{tag}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())

    def test_can_create_ticket_url_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        data = {
            "ticket_url": "www.example.com",
        }
        response = self.client.put(path=f"/api/v1/incidents/{incident_pk}/ticket_url/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(id=incident_pk).ticket_url, data["ticket_url"])

    def test_can_get_my_incidents(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        other_incident_pk = StatefulIncidentFactory().pk

        response = self.client.get(path="/api/v1/incidents/mine/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        response_pks = [incident["pk"] for incident in response.data["results"]]
        self.assertIn(incident_pk, response_pks)
        self.assertNotIn(other_incident_pk, response_pks)

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
        self.assertTrue(Incident.objects.filter(id=response.data["pk"]).exists())
        incident = Incident.objects.get(id=response.data["pk"])
        # Check that we have made the correct Tag
        tag = data["tags"][0]["tag"]
        key, value = Tag.split(tag)
        self.assertTrue(Tag.objects.filter(key=key, value=value).exists())
        tag = Tag.objects.get(key=key, value=value)
        # Check that incident and tag are linked
        self.assertTrue(IncidentTagRelation.objects.filter(incident=incident).filter(tag=tag).exists())

    def test_can_get_all_source_types(self):
        source_type_names = set([type.name for type in SourceSystemType.objects.all()])

        response = self.client.get(path=f"/api/v1/incidents/source-types/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_types = set([type["name"] for type in response.data])
        self.assertEqual(response_types, source_type_names)

    def test_can_get_specific_source_type(self):
        response = self.client.get(path=f"/api/v1/incidents/source-types/{self.source.type.name}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.source.type.name)

    def test_can_create_source_type(self):
        data = {
            "name": "test",
        }
        response = self.client.post(path=f"/api/v1/incidents/source-types/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SourceSystemType.objects.filter(name=data["name"]).exists())

    def test_can_get_all_source_systems(self):
        source_pks = set([source.pk for source in SourceSystem.objects.all()])

        response = self.client.get(path=f"/api/v1/incidents/sources/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_source_pks = set([source["pk"] for source in response.data])
        self.assertEqual(response_source_pks, source_pks)

    def test_can_get_specific_source_system(self):
        response = self.client.get(path=f"/api/v1/incidents/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], self.source.pk)

    def test_can_create_source_system(self):
        # Only admins can create sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newtest",
            "type": self.source.type.name,
        }
        response = self.client.post(path=f"/api/v1/incidents/sources/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SourceSystem.objects.filter(name=data["name"]).exists())

    def test_can_update_source_system(self):
        # Only admins can update sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newname",
        }
        response = self.client.put(path=f"/api/v1/incidents/sources/{self.source.pk}/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SourceSystem.objects.get(id=self.source.pk).name, data["name"])


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
        self.assertEqual(response.data["results"][0]["pk"], self.open_pk)

    def test_open_false_returns_only_closed_incidents(self):
        response = self.client.get("/api/v1/incidents/?open=false")
        self.assertEqual(response.data["results"][0]["pk"], self.closed_pk)

    def test_stateful_false_returns_only_stateless_incidents(self):
        response = self.client.get("/api/v1/incidents/?stateful=false")
        self.assertEqual(response.data["results"][0]["pk"], self.stateless_pk)

    def test_stateful_true_returns_only_stateful_incidents(self):
        response = self.client.get("/api/v1/incidents/?stateful=true")
        response_pks = set([result["pk"] for result in response.data["results"]])
        self.assertEqual(response_pks, set([self.open_pk, self.closed_pk]))

    def test_open_true_and_stateful_true_returns_only_open_incidents(self):
        response = self.client.get("/api/v1/incidents/?open=true&stateful=true")
        self.assertEqual(response.data["results"][0]["pk"], self.open_pk)

    def test_open_true_and_stateful_false_returns_no_incidents(self):
        response = self.client.get("/api/v1/incidents/?stateful=false&open=true")
        self.assertEqual(len(response.data["results"]), 0, msg=response.data)

    def test_open_false_and_stateful_true_returns_only_closed_incidents(self):
        response = self.client.get("/api/v1/incidents/?open=false&stateful=true")
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
        self.add_open_incident_with_start_event_and_tag()
        incident_pks = list(Incident.objects.all().values_list("pk", flat=True))

        response = self.client.get(path="/api/v2/incidents/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        response_pks = [incident["pk"] for incident in response.data["results"]]
        self.assertEqual(response_pks, incident_pks)

    def test_can_get_incident_by_incident_description(self):
        pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        response = self.client.get(path="/api/v2/incidents/?search=incident1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["pk"], pk)

    def test_can_get_incident_by_event_description(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        self.add_event(incident_pk=incident_pk, description="event1")
        response = self.client.get(path="/api/v2/incidents/?search=event1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_can_get_multiple_incidents_by_incident_description(self):
        incident_pk1 = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        incident_pk2 = self.add_open_incident_with_start_event_and_tag(description="incident2").pk
        self.add_event(incident_pk=incident_pk1, description="event1")
        self.add_event(incident_pk=incident_pk2, description="event2")
        response = self.client.get(path="/api/v2/incidents/?search=incident")
        response_pks = set([incident["pk"] for incident in response.data["results"]])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_pks, set([incident_pk1, incident_pk2]))

    def test_can_get_multiple_incidents_by_incident_description_and_event_description(self):
        incident_pk1 = self.add_open_incident_with_start_event_and_tag(description="target_incident").pk
        incident_pk2 = self.add_open_incident_with_start_event_and_tag(description="incident2").pk
        self.add_event(incident_pk=incident_pk1, description="event1")
        self.add_event(incident_pk=incident_pk2, description="target_event")
        response = self.client.get(path="/api/v2/incidents/?search=target")
        response_pks = set([incident["pk"] for incident in response.data["results"]])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
        self.assertTrue(Incident.objects.filter(id=response.data["pk"]).exists())
        incident = Incident.objects.get(id=response.data["pk"])
        # Check that we have made the correct Tag
        tag = data["tags"][0]["tag"]
        key, value = Tag.split(tag)
        self.assertTrue(Tag.objects.filter(key=key, value=value).exists())
        tag = Tag.objects.get(key=key, value=value)
        # Check that incident and tag are linked
        self.assertTrue(IncidentTagRelation.objects.filter(incident=incident).filter(tag=tag).exists())

    def test_can_update_incident_level(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        incident_path = reverse("v2:incident:incident-detail", args=[incident_pk])
        response = self.client.patch(
            path=incident_path,
            data={
                "level": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(pk=incident_pk).level, 2)

    def test_can_get_all_acknowledgements_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident = ack.event.incident
        ack_pks = list(incident.acks.all().values_list("pk", flat=True))

        response = self.client.get(path=f"/api/v2/incidents/{incident.pk}/acks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_pks = [ack["pk"] for ack in response.data]
        self.assertEqual(response_pks, ack_pks)
        event_types = [ack["event"]["type"]["value"] for ack in response.data]
        self.assertEqual(set(event_types), {"ACK"})

    def test_can_get_specific_acknowledgement_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident_pk = ack.event.incident.pk
        response = self.client.get(path=f"/api/v2/incidents/{incident_pk}/acks/{ack.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["event"]["pk"], ack.pk)
        self.assertEqual(response.data["event"]["type"]["value"], "ACK")

    def test_can_create_acknowledgement_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "type": "STA",
                "description": "acknowledgement",
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident.pk}/acks/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(incident.events.filter(id=response.data["pk"]).exists())
        self.assertTrue(Acknowledgement.objects.filter(event_id=response.data["pk"]).exists())

    def test_can_update_acknowledgement_of_incident(self):
        ack = self.add_acknowledgement_with_incident_and_event()
        incident = ack.event.incident
        data = {
            "expiration": (now() + datetime.timedelta(days=3)).isoformat(),
        }
        response = self.client.put(path=f"/api/v2/incidents/{incident.pk}/acks/{ack.pk}/", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            incident.events.get(pk=ack.pk).ack.expiration, datetime.datetime.fromisoformat(data["expiration"])
        )

    def test_can_get_all_events_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        event_pks = list(incident.events.all().values_list("pk", flat=True))

        response = self.client.get(path=f"/api/v2/incidents/{incident.pk}/events/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_pks = [ack["pk"] for ack in response.data]
        self.assertEqual(response_pks, event_pks)

    def test_can_get_specific_event_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        event_pk = incident.events.first().pk
        response = self.client.get(path=f"/api/v2/incidents/{incident.pk}/events/{event_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], event_pk)

    def test_can_create_event_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = {
            "timestamp": "2022-08-02T13:45:44.056Z",
            "type": "OTH",
            "description": "event",
        }
        response = self.client.post(path=f"/api/v2/incidents/{incident.pk}/events/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(incident.events.filter(id=response.data["pk"]).exists())

    def test_can_get_all_tags_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tags = [str(relation.tag) for relation in incident.incident_tag_relations.all()]

        response = self.client.get(path=f"/api/v2/incidents/{incident.pk}/tags/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_tags = [tag["tag"] for tag in response.data]
        self.assertEqual(response_tags, tags)

    def test_can_get_specific_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tag = incident.incident_tag_relations.first().tag
        response = self.client.get(path=f"/api/v2/incidents/{incident.pk}/tags/{tag}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tag"], str(tag))

    def test_can_create_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = {
            "tag": "c=d",
        }

        response = self.client.post(path=f"/api/v2/incidents/{incident.pk}/tags/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        incident_tags = [str(relation.tag) for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertIn(data["tag"], incident_tags)

    def test_cannot_create_tag_of_incident_with_invalid_key(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = {
            "tag": "???=d",
        }

        response = self.client.post(path=f"/api/v2/incidents/{incident.pk}/tags/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        incident_tags = [str(relation.tag) for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertNotIn(data["tag"], incident_tags)

    def test_can_delete_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tag = incident.incident_tag_relations.first().tag

        response = self.client.delete(path=f"/api/v2/incidents/{incident.pk}/tags/{tag}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())

    def test_can_create_ticket_url_of_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        data = {
            "ticket_url": "www.example.com",
        }
        response = self.client.put(path=f"/api/v2/incidents/{incident_pk}/ticket_url/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(id=incident_pk).ticket_url, data["ticket_url"])

    def test_can_get_my_incidents(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        other_incident_pk = StatefulIncidentFactory().pk

        response = self.client.get(path="/api/v2/incidents/mine/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        response_pks = [incident["pk"] for incident in response.data["results"]]
        self.assertIn(incident_pk, response_pks)
        self.assertNotIn(other_incident_pk, response_pks)

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
        self.assertTrue(Incident.objects.filter(id=response.data["pk"]).exists())
        incident = Incident.objects.get(id=response.data["pk"])
        # Check that we have made the correct Tag
        tag = data["tags"][0]["tag"]
        key, value = Tag.split(tag)
        self.assertTrue(Tag.objects.filter(key=key, value=value))
        tag = Tag.objects.get(key=key, value=value)
        # Check that incident and tag are linked
        self.assertTrue(IncidentTagRelation.objects.filter(incident=incident).filter(tag=tag).exists())

    def test_can_get_all_events(self):
        self.add_open_incident_with_start_event_and_tag()
        event_pks = list(Event.objects.all().values_list("pk", flat=True))

        response = self.client.get(path=f"/api/v2/incidents/events/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        response_pks = [ack["pk"] for ack in response.data["results"]]
        self.assertEqual(response_pks, event_pks)

    def test_can_get_all_source_types(self):
        source_type_names = set([type.name for type in SourceSystemType.objects.all()])

        response = self.client.get(path=f"/api/v2/incidents/source-types/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_types = set([type["name"] for type in response.data])
        self.assertEqual(response_types, source_type_names)

    def test_can_get_specific_source_type(self):
        response = self.client.get(path=f"/api/v2/incidents/source-types/{self.source.type.name}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.source.type.name)

    def test_can_create_source_type(self):
        data = {
            "name": "test",
        }
        response = self.client.post(path=f"/api/v2/incidents/source-types/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SourceSystemType.objects.filter(name=data["name"]).exists())

    def test_can_get_all_source_systems(self):
        source_pks = set([source.pk for source in SourceSystem.objects.all()])

        response = self.client.get(path=f"/api/v2/incidents/sources/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_source_pks = set([source["pk"] for source in response.data])
        self.assertEqual(response_source_pks, source_pks)

    def test_can_get_specific_source_system(self):
        response = self.client.get(path=f"/api/v2/incidents/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], self.source.pk)

    def test_can_create_source_system(self):
        # Only admins can create sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newtest",
            "type": self.source.type.name,
        }
        response = self.client.post(path=f"/api/v2/incidents/sources/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SourceSystem.objects.filter(name=data["name"]).exists())

    def test_can_update_source_system(self):
        # Only admins can update sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newname",
        }
        response = self.client.put(path=f"/api/v2/incidents/sources/{self.source.pk}/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SourceSystem.objects.get(id=self.source.pk).name, data["name"])


class BulkAcknowledgementViewSetTestCase(APITestCase):
    def setUp(self):
        disconnect_signals()
        self.user = BaseUserFactory(username="user1")
        self.client.force_authenticate(user=self.user)
        self.ack_data = {
            "event": {
                "timestamp": "2022-08-02T13:04:03.529Z",
                "description": "acknowledgement",
            },
            "expiration": "2022-08-03T13:04:03.529Z",
        }

    def tearDown(self):
        connect_signals()

    def test_can_bulk_create_acknowledgements_for_incidents_with_valid_ids(self):
        incident_1 = StatefulIncidentFactory()
        incident_2 = StatefulIncidentFactory()
        data = {
            "ids": [incident_1.pk, incident_2.pk],
            "ack": self.ack_data,
        }

        response = self.client.post(path=f"/api/v2/incidents/acks/bulk/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        incident_1_changes = response.data["changes"][str(incident_1.pk)]
        self.assertEqual(incident_1_changes["status"], status.HTTP_201_CREATED)
        self.assertEqual(incident_1_changes["ack"]["event"]["type"]["value"], "ACK")
        self.assertEqual(incident_1_changes["errors"], None)

        incident_2_changes = response.data["changes"][str(incident_2.pk)]
        self.assertEqual(incident_2_changes["status"], status.HTTP_201_CREATED)
        self.assertEqual(incident_2_changes["ack"]["event"]["type"]["value"], "ACK")
        self.assertEqual(incident_2_changes["errors"], None)

        self.assertTrue(incident_1.events.filter(type="ACK").exists())
        self.assertTrue(incident_2.events.filter(type="ACK").exists())

    def test_cannot_bulk_create_acknowledgements_for_incidents_with_all_invalid_ids(self):
        highest_incident_pk = Incident.objects.last().id if Incident.objects.exists() else 0
        invalid_incident_1_pk = highest_incident_pk + 1
        invalid_incident_2_pk = highest_incident_pk + 2
        data = {
            "ids": [invalid_incident_1_pk, invalid_incident_2_pk],
            "ack": self.ack_data,
        }

        response = self.client.post(path=f"/api/v2/incidents/acks/bulk/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_incident_1_changes = response.data["changes"][str(invalid_incident_1_pk)]
        self.assertEqual(invalid_incident_1_changes["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_incident_1_changes["ack"], None)
        self.assertTrue(invalid_incident_1_changes["errors"])

        invalid_incident_2_changes = response.data["changes"][str(invalid_incident_2_pk)]
        self.assertEqual(invalid_incident_2_changes["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_incident_2_changes["ack"], None)
        self.assertTrue(invalid_incident_2_changes["errors"])

        self.assertFalse(Acknowledgement.objects.filter(event__incident_id=invalid_incident_1_pk).exists())
        self.assertFalse(Acknowledgement.objects.filter(event__incident_id=invalid_incident_2_pk).exists())

    def test_can_partially_bulk_create_acknowledgements_for_incidents_with_some_valid_ids(self):
        incident_1 = StatefulIncidentFactory()
        highest_incident_pk = Incident.objects.last().id
        invalid_incident_2_pk = highest_incident_pk + 1
        data = {
            "ids": [incident_1.pk, invalid_incident_2_pk],
            "ack": self.ack_data,
        }

        response = self.client.post(path=f"/api/v2/incidents/acks/bulk/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        incident_1_changes = response.data["changes"][str(incident_1.pk)]
        self.assertEqual(incident_1_changes["status"], status.HTTP_201_CREATED)
        self.assertEqual(incident_1_changes["ack"]["event"]["type"]["value"], "ACK")
        self.assertEqual(incident_1_changes["errors"], None)

        invalid_incident_2_changes = response.data["changes"][str(invalid_incident_2_pk)]
        self.assertEqual(invalid_incident_2_changes["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_incident_2_changes["ack"], None)
        self.assertTrue(invalid_incident_2_changes["errors"])

        self.assertTrue(incident_1.events.filter(type="ACK").exists())
        self.assertFalse(Acknowledgement.objects.filter(event__incident_id=invalid_incident_2_pk).exists())
