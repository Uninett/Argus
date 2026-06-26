from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.util.testing import disconnect_signals, connect_signals
from argus.incident.factories import (
    SourceSystemFactory,
    SourceUserFactory,
    StatefulIncidentFactory,
    StatelessIncidentFactory,
    TagFactory,
    create_dead_source,
    create_fake_incident,
)
from argus.incident.models import Incident, Event, SourceSystem, Tag, get_or_create_default_instances
from argus.incident.heartbeat_utils import _get_or_create_incident_for_dead_source


class IncidentQuerySetTestCase(TestCase):
    def setUp(self):
        disconnect_signals()
        # Lock in timestamps
        self.timestamp = timezone.now()
        # We don't care about source but let's ensure it is unique
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(user=source_user)
        self.incident1 = StatelessIncidentFactory(source=self.source, start_time=self.timestamp, ticket_url="")
        self.incident2 = StatefulIncidentFactory(source=self.source, start_time=self.timestamp, ticket_url="")
        self.incident3 = StatefulIncidentFactory(source=self.source, start_time=self.timestamp, ticket_url="")
        self.incident4 = StatefulIncidentFactory(source=self.source, start_time=self.timestamp)
        self.incident4.end_time = self.timestamp
        self.incident4.save()

    def tearDown(self):
        connect_signals()

    def test_stateful(self):
        result = Incident.objects.stateful()
        self.assertNotIn(self.incident1, result)

    def test_stateless(self):
        result = Incident.objects.stateless()
        self.assertEqual(result.get(), self.incident1)

    def test_open(self):
        result = Incident.objects.open()
        self.assertEqual(set(result), set((self.incident2, self.incident3)))

    def test_closed(self):
        result = Incident.objects.closed()
        self.assertEqual(result.get(), self.incident4)

    def test_acked(self):
        incident_acked = StatefulIncidentFactory(source=self.source)
        user = PersonUserFactory()
        incident_acked.create_ack(user)
        result = Incident.objects.acked()
        self.assertEqual(result.get(), incident_acked)

    def test_not_acked(self):
        incident_acked = StatefulIncidentFactory(source=self.source)
        user = PersonUserFactory()
        # Create an expired ack
        incident_acked.create_ack(user, expiration=self.timestamp)
        result = Incident.objects.not_acked()
        self.assertEqual(set(result), set(Incident.objects.all()))

    def test_has_ticket(self):
        result = Incident.objects.has_ticket()
        self.assertEqual(result.get(), self.incident4)

    def test_lacks_ticket(self):
        result = Incident.objects.lacks_ticket()
        self.assertEqual(set(result), set((self.incident1, self.incident2, self.incident3)))


class IncidentQuerySetUpdatingTestCase(TestCase):
    def setUp(self):
        disconnect_signals()
        # Lock in timestamps
        self.timestamp = timezone.now()
        # We don't care about source but let's ensure it is unique
        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        self.incident1 = StatelessIncidentFactory(source=source, start_time=self.timestamp, ticket_url="")
        self.incident2 = StatefulIncidentFactory(source=source, start_time=self.timestamp, ticket_url="")
        self.incident3 = StatefulIncidentFactory(source=source, start_time=self.timestamp, ticket_url="")
        self.incident4 = StatefulIncidentFactory(source=source, start_time=self.timestamp, end_time=self.timestamp)
        self.source = source
        self.user = PersonUserFactory()

    def tearDown(self):
        connect_signals()

    @tag("bulk")
    def test_create_acks(self):
        qs = Incident.objects.filter(id__in=(self.incident3.id, self.incident4.id))
        qs.create_acks(self.user)
        result = set(Incident.objects.acked())
        self.assertEqual(result, set(qs.all()))

    @tag("bulk")
    def test_create_events(self):
        qs = Incident.objects.filter(id__in=(self.incident3.id, self.incident4.id))
        qs.create_events(self.user, Event.Type.OTHER, description="foo")
        result = set(e.incident for e in Event.objects.filter(type=Event.Type.OTHER))
        self.assertEqual(result, set(qs.all()))

    @tag("bulk")
    def test_update_ticket_url(self):
        qs = Incident.objects.filter(id__in=(self.incident1.id, self.incident2.id))
        qs.update_ticket_url(self.user, "http://vg.no")
        result = qs.has_ticket()
        self.assertEqual(set(result), set(qs.all()))

    @tag("bulk")
    def test_close_incidents(self):
        qs = Incident.objects.filter(id__in=(self.incident2.id, self.incident3.id))
        qs.close(self.user, description="Boo")
        result = set(e.incident for e in Event.objects.filter(type=Event.Type.CLOSE, description="Boo"))
        self.assertEqual(result, set(qs.all()))

    @tag("bulk")
    def test_reopen_incidents(self):
        self.incident2.set_closed(self.user)
        self.incident3.set_closed(self.user)
        qs = Incident.objects.filter(id__in=(self.incident2.id, self.incident3.id))
        qs.reopen(self.user, description="Bar")
        result = set(e.incident for e in Event.objects.filter(type=Event.Type.REOPEN, description="Bar"))
        self.assertEqual(result, set(qs.all()))


class TestTagQuerySetMethods(TestCase):
    def test_from_tags_converts_tagstrings_to_existing_tags(self):
        tag1 = TagFactory()
        tag2 = TagFactory()
        tag3 = TagFactory()
        result = Tag.objects.from_tags(tag1.representation, tag2.representation)
        self.assertNotIn(tag3, result)
        self.assertEqual(set(tag1.representation, tag2.representation), result)

    def test_from_tag_keys(self):
        tag1 = TagFactory(key="foo", value="foo")
        tag2 = TagFactory(key="foo", value="bar")
        tag3 = TagFactory(key="xux", value="foo")
        result = Tag.objects.from_tag_keys(tag1.key)
        self.assertNotIn(tag3, result)
        self.assertEqual(set(tag1.representation, tag2.representation), set(result))


class MakeImmutableFixtures:
    def setUp(self):
        disconnect_signals()
        _, sst, self.owner_source = get_or_create_default_instances()
        self.alive_source = SourceSystemFactory(
            name="spring_blossom", last_seen=timezone.now(), heartbeat_frequency=timedelta(days=1)
        )
        self.irrelevant_incident = create_fake_incident(source=self.owner_source.name, tags=["test=test"])

    def tearDown(self):
        connect_signals()


class TestSourceSystemQuerySet(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_when_no_dead_sources_return_empty_queryset(self):
        result = SourceSystem.objects.dead(timezone.now())
        self.assertFalse(result.exists())

    def test_when_a_dead_source_return_annotated_queryset(self):
        zombie_source, timestamp = create_dead_source("zombie_walking")
        result = SourceSystem.objects.dead(timestamp)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result[0].name, "zombie_walking")
        self.assertTrue(result[0].next_heartbeat)


class TestIncidentQuerySetHeartbeatIncidents(MakeImmutableFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.zombie_source, self.timestamp = create_dead_source("zombie_walking")

    def test_when_no_heartbeat_incidents_returns_empty_queryset(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().exists())

    def test_when_heartbeat_incidents_exist_return_them(self):
        incident = _get_or_create_incident_for_dead_source(
            self.zombie_source, incident_owner=self.owner_source, timestamp=self.timestamp
        )
        result = Incident.objects.heartbeat_incidents()
        self.assertIn(incident, result)
        self.assertNotIn(self.irrelevant_incident, result)
