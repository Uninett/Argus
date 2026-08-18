from django.urls import reverse
from django.test import override_settings, tag

from rest_framework import status
from rest_framework.test import APITestCase

from argus.auth.factories import (
    AdminUserFactory,
    PersonUserFactory,
    SourceUserFactory,
)
from argus.filter.factories import FilterFactory
from argus.incident.factories import (
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
    Tag,
    get_or_create_default_instances,
)
from argus.notificationprofile.models import Filter
from argus.util.testing import disconnect_signals, connect_signals


API_VERSION = "v3"
API_PATH = f"/api/{API_VERSION}/incidents"


def add_open_incident_with_start_event_and_tag(source, description="incident"):
    incident = StatefulIncidentFactory(source=source, description=description)
    tag = TagFactory(key="a", value="b")
    IncidentTagRelationFactory(incident=incident, tag=tag)
    incident.create_first_event()
    return incident


class IncidentAPITestCase(APITestCase):
    def setUp(self):
        disconnect_signals()
        source_type = SourceSystemTypeFactory()
        self.user = SourceUserFactory()
        self.source = SourceSystemFactory(type=source_type, user=self.user)
        self.admin = AdminUserFactory()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        connect_signals()


class IncidentViewSetDeleteTestCase(IncidentAPITestCase):
    @override_settings(INDELIBLE_INCIDENTS=True)
    def test_cannot_delete_incident_if_indelible_is_True(self):
        incident_pk = add_open_incident_with_start_event_and_tag(self.source).pk
        # source
        response = self.client.delete(path=f"{API_PATH}/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # superuser
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(path=f"{API_PATH}/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @override_settings(INDELIBLE_INCIDENTS=False)
    def test_superuser_can_delete_incident_if_indelible_is_False(self):
        incident_pk = add_open_incident_with_start_event_and_tag(self.source).pk
        self.client.force_authenticate(user=self.admin)
        self.assertTrue(Incident.objects.filter(pk=incident_pk).exists())
        response = self.client.delete(path=f"{API_PATH}/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Incident.objects.filter(pk=incident_pk).exists())

    @override_settings(INDELIBLE_INCIDENTS=False)
    def test_source_can_delete_owned_incident_if_indelible_is_False(self):
        incident_pk = add_open_incident_with_start_event_and_tag(self.source).pk
        self.assertTrue(Incident.objects.filter(pk=incident_pk).exists())
        response = self.client.delete(path=f"{API_PATH}/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Incident.objects.filter(pk=incident_pk).exists())

    @override_settings(INDELIBLE_INCIDENTS=False)
    def test_can_delete_acknowledged_incidente(self):
        incident = add_open_incident_with_start_event_and_tag(self.source)
        self.assertTrue(Incident.objects.filter(pk=incident.pk).exists())
        ack = incident.create_ack(actor=self.user)
        self.assertTrue(Acknowledgement.objects.filter(pk=ack.pk).exists())
        response = self.client.delete(path=f"{API_PATH}/{incident.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Incident.objects.filter(pk=incident.pk).exists())
        self.assertFalse(Acknowledgement.objects.filter(pk=ack.pk).exists())

    @override_settings(INDELIBLE_INCIDENTS=False)
    def test_source_cannot_delete_unowned_incident_if_indelible_is_False(self):
        incident_pk = add_open_incident_with_start_event_and_tag(self.source).pk
        self.assertTrue(Incident.objects.filter(pk=incident_pk).exists())

        source_type = SourceSystemTypeFactory()
        user = SourceUserFactory()
        SourceSystemFactory(type=source_type, user=user)
        self.client.force_authenticate(user=user)

        response = self.client.delete(path=f"{API_PATH}/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Incident.objects.filter(pk=incident_pk).exists())

    @override_settings(INDELIBLE_INCIDENTS=False)
    def test_nonsource_nonsuperuser_cannot_delete_incident(self):
        incident_pk = add_open_incident_with_start_event_and_tag(self.source).pk
        self.assertTrue(Incident.objects.filter(pk=incident_pk).exists())

        user = PersonUserFactory()
        self.client.force_authenticate(user=user)

        response = self.client.delete(path=f"{API_PATH}/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Incident.objects.filter(pk=incident_pk).exists())


@tag("queryset-filter")
class IncidentFilterByFilterPkTestCase(IncidentAPITestCase):
    def setUp(self):
        super().setUp()
        self.open_pk = StatefulIncidentFactory(source=self.source).pk
        self.closed_pk = StatefulIncidentFactory(
            start_time="2022-05-23T13:07:29.254Z", end_time="2022-05-24T13:07:29.254Z", source=self.source
        ).pk
        self.stateless_pk = StatelessIncidentFactory(source=self.source).pk

    def test_filter_by_filter_pk_returns_no_incidents_on_non_existent_filter(self):
        non_existent_filter_pk = Filter.objects.last().pk + 1 if Filter.objects.exists() else 1
        response = self.client.get(f"{API_PATH}/?filter_pk={non_existent_filter_pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["results"])

    def test_filter_by_filter_pk_raises_error_on_invalid_decimal_pk(self):
        response = self.client.get(f"{API_PATH}/?filter_pk=1.5")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_filter_pk_returns_no_incidents_on_someone_elses_filter(self):
        someone_elses_filter_pk = FilterFactory().pk
        response = self.client.get(f"{API_PATH}/?filter_pk={someone_elses_filter_pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["results"])


class IncidentViewSetTestCase(IncidentAPITestCase):
    def add_open_incident_with_start_event_and_tag(self, description="incident"):
        return add_open_incident_with_start_event_and_tag(self.source, description=description)

    def add_event(self, incident_pk, description="event", type=Event.Type.OTHER):
        return EventFactory(incident_id=incident_pk, description=description, type=type)

    def test_can_get_all_incidents(self):
        self.add_open_incident_with_start_event_and_tag()
        incident_pks = list(Incident.objects.all().values_list("pk", flat=True))

        response = self.client.get(path=API_PATH + "/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Paging, so check "results"
        response_pks = [incident["pk"] for incident in response.data["results"]]
        self.assertEqual(response_pks, incident_pks)

    def test_can_get_incident_by_incident_description(self):
        pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        response = self.client.get(path=f"{API_PATH}/?search=incident1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["pk"], pk)

    def test_can_get_incident_by_event_description(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        self.add_event(incident_pk=incident_pk, description="event1")
        response = self.client.get(path=f"{API_PATH}/?search=event1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_cannot_get_incident_by_nonexisting_description(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        self.add_event(incident_pk=incident_pk, description="event1")
        response = self.client.get(path=f"{API_PATH}/?search=not_a_description")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)
        self.assertEqual(response.data["results"], [])

    def test_can_get_incident_by_incident_description_and_event_description(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        self.add_event(incident_pk=incident_pk, description="event")
        self.add_open_incident_with_start_event_and_tag(description="incident2")
        self.add_event(incident_pk=incident_pk, description="event")
        response = self.client.get(path=f"{API_PATH}/?search=incident1,event")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["pk"], incident_pk)

    def test_can_get_multiple_incidents_by_incident_description(self):
        incident_pk1 = self.add_open_incident_with_start_event_and_tag(description="incident1").pk
        incident_pk2 = self.add_open_incident_with_start_event_and_tag(description="incident2").pk
        self.add_event(incident_pk=incident_pk1, description="event1")
        self.add_event(incident_pk=incident_pk2, description="event2")
        response = self.client.get(path=f"{API_PATH}/?search=incident")
        response_pks = set([incident["pk"] for incident in response.data["results"]])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_pks, set([incident_pk1, incident_pk2]))

    def test_can_get_multiple_incidents_by_incident_description_and_event_description(self):
        incident_pk1 = self.add_open_incident_with_start_event_and_tag(description="target_incident").pk
        incident_pk2 = self.add_open_incident_with_start_event_and_tag(description="incident2").pk
        self.add_event(incident_pk=incident_pk1, description="event1")
        self.add_event(incident_pk=incident_pk2, description="target_event")
        response = self.client.get(path=f"{API_PATH}/?search=target")
        response_pks = set([incident["pk"] for incident in response.data["results"]])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_pks, set([incident_pk1, incident_pk2]))

    def test_can_get_specific_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path=f"{API_PATH}/{incident_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], incident_pk)

    def test_can_create_incident_with_tag(self):
        # Minimal data to post that has tags
        data = {
            "start_time": "2021-08-04T09:13:55.908Z",
            "end_time": "2021-08-04T09:13:55.908Z",
            "description": "incident",
            "level": 1,
            "tags": ["a=b"],
        }

        response = self.client.post(path=API_PATH + "/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that we have made the correct Incident
        self.assertTrue(Incident.objects.filter(id=response.data["pk"]).exists())
        incident = Incident.objects.get(id=response.data["pk"])
        # Check that we have made the correct Tag
        tag = data["tags"][0]
        key, value = Tag.split(tag)
        self.assertTrue(Tag.objects.filter(key=key, value=value).exists())
        tag = Tag.objects.get(key=key, value=value)
        # Check that incident and tag are linked
        self.assertTrue(IncidentTagRelation.objects.filter(incident=incident).filter(tag=tag).exists())

    def test_can_update_incident_level(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        incident_path = reverse(f"{API_VERSION}:incident:incident-detail", args=[incident_pk])
        response = self.client.patch(
            path=incident_path,
            data={
                "level": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(pk=incident_pk).level, 2)

    def test_can_update_incident_metadata(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        start_metadata = {"foo": "xux"}
        incident.metadata = start_metadata
        incident.save()
        incident_path = reverse(f"{API_VERSION}:incident:incident-detail", args=[incident.pk])
        changed_metadata = {"bar": "gurba"}
        response = self.client.patch(
            path=incident_path,
            data={
                "metadata": changed_metadata,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        changed_incident = Incident.objects.get(pk=incident.pk)
        self.assertNotEqual(changed_incident.metadata, start_metadata)
        self.assertEqual(changed_incident.metadata, changed_metadata)

    def test_can_update_incident_description(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        incident_path = reverse(f"{API_VERSION}:incident:incident-detail", args=[incident_pk])
        response = self.client.patch(
            path=incident_path,
            data={
                "description": "new description",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(pk=incident_pk).description, "new description")


class IncidentViewSetTicketUrlTestCase(IncidentAPITestCase):
    def test_can_create_ticket_url_of_incident(self):
        incident_pk = add_open_incident_with_start_event_and_tag(self.source).pk
        data = {
            "ticket_url": "www.example.com",
        }
        response = self.client.put(path=f"{API_PATH}/{incident_pk}/ticket_url/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Incident.objects.get(id=incident_pk).ticket_url, data["ticket_url"])


@tag("integration", "api", "db")
class IncidentTagViewSetTestCase(IncidentAPITestCase):
    def add_open_incident_with_start_event_and_tag(self, description="incident"):
        return add_open_incident_with_start_event_and_tag(self.source, description=description)

    def test_can_get_all_tags_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tags = [str(relation.tag) for relation in incident.incident_tag_relations.all()]

        response = self.client.get(path=f"{API_PATH}/{incident.pk}/tags/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, tags)

    def test_can_get_specific_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tag = incident.incident_tag_relations.first().tag
        response = self.client.get(path=f"{API_PATH}/{incident.pk}/tags/{tag}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], str(tag))

    def test_cannot_get_tag_unknown_to_specific_incident(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path=f"{API_PATH}/{incident_pk}/tags/nonenxistent=tag/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"].code, "not_found")

    def test_cannot_get_invalid_tag(self):
        incident_pk = self.add_open_incident_with_start_event_and_tag().pk
        response = self.client.get(path=f"{API_PATH}/{incident_pk}/tags/foo/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.data[0]
        self.assertEqual(error.code, "invalid")

    def test_can_create_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = ["c=d"]

        response = self.client.post(path=f"{API_PATH}/{incident.pk}/tags/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        incident_tags = [str(relation.tag) for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertIn(data[0], incident_tags)

    def test_cannot_create_tag_of_incident_with_invalid_key(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        data = ["???=d"]

        response = self.client.post(path=f"{API_PATH}/{incident.pk}/tags/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        incident_tags = [str(relation.tag) for relation in IncidentTagRelation.objects.filter(incident=incident)]
        self.assertNotIn(data[0], incident_tags)

    def test_can_delete_tag_of_incident(self):
        incident = self.add_open_incident_with_start_event_and_tag()
        tag = incident.incident_tag_relations.first().tag

        response = self.client.delete(path=f"{API_PATH}/{incident.pk}/tags/{tag}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # The tag should still exist..
        self.assertTrue(Tag.objects.filter(pk=tag.pk).exists())
        # .. but the incident shouldn't know of it anymore
        self.assertNotIn(tag.representation, incident.deprecated_tags)


class SourceLockedIncidentViewSetTestCase(IncidentAPITestCase):
    def test_can_get_my_incidents(self):
        incident_pk = add_open_incident_with_start_event_and_tag(self.source).pk
        _, _, argus = get_or_create_default_instances()
        other_incident_pk = add_open_incident_with_start_event_and_tag(argus).pk

        response = self.client.get(path=f"{API_PATH}/mine/")

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
            "tags": ["c=d"],
        }

        response = self.client.post(path=f"{API_PATH}/mine/", data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that we have made the correct Incident
        self.assertTrue(Incident.objects.filter(id=response.data["pk"]).exists())
        incident = Incident.objects.get(id=response.data["pk"])
        # Check that we have made the correct Tag
        tag = data["tags"][0]
        key, value = Tag.split(tag)
        self.assertTrue(Tag.objects.filter(key=key, value=value))
        tag = Tag.objects.get(key=key, value=value)
        # Check that incident and tag are linked
        self.assertTrue(IncidentTagRelation.objects.filter(incident=incident).filter(tag=tag).exists())


class SourceSystemViewSetTestCase(IncidentAPITestCase):
    def test_can_get_all_source_systems(self):
        source_pks = set([source.pk for source in SourceSystem.objects.all()])

        response = self.client.get(path=f"{API_PATH}/sources/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_source_pks = set([source["pk"] for source in response.data])
        self.assertEqual(response_source_pks, source_pks)

    def test_can_get_specific_source_system(self):
        response = self.client.get(path=f"{API_PATH}/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], self.source.pk)

    def test_can_create_source_system(self):
        # Only admins can create sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newtest",
            "type": self.source.type.name,
        }
        response = self.client.post(path=f"{API_PATH}/sources/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SourceSystem.objects.filter(name=data["name"]).exists())

    def test_can_update_source_system(self):
        # Only admins can update sources
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "newname",
        }
        response = self.client.put(path=f"{API_PATH}/sources/{self.source.pk}/", data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SourceSystem.objects.get(id=self.source.pk).name, data["name"])
