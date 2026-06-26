from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now as tznow

from argus.incident.factories import SourceSystemFactory, create_dead_source, create_fake_incident
from argus.incident.heartbeat_utils import (
    SOURCE_TAG_KEY,
    HEARTBEAT_TAG,
    _close_incidents_whose_sources_are_alive_again,
    _create_incidents_for_dead_sources,
    _get_or_create_incident_for_dead_source,
    sync_heartbeats_with_heartbeat_incidents,
)
from argus.incident.models import Incident, get_or_create_default_instances


class MakeImmutableFixtures:
    def setUp(self):
        _, sst, self.owner_source = get_or_create_default_instances()
        self.alive_source = SourceSystemFactory(
            name="spring_blossom", last_seen=tznow(), heartbeat_frequency=timedelta(days=1)
        )
        self.irrelevant_incident = create_fake_incident(source=self.owner_source.name, tags=["test=test"])


class TestCreateIncidentForDeadSource(MakeImmutableFixtures, TestCase):
    def test_when_source_is_not_dead_we_create_nothing(self):
        result = _get_or_create_incident_for_dead_source(
            self.alive_source, incident_owner=self.owner_source, timestamp=self.alive_source.last_seen
        )
        self.assertEqual(result, None)

    def test_when_source_is_dead_created_incident_has_correct_description_and_tags(self):
        zombie_source, timestamp = create_dead_source("zombie_walking")
        incident = _get_or_create_incident_for_dead_source(
            zombie_source, incident_owner=self.owner_source, timestamp=timestamp
        )
        self.assertEqual(incident.description, f"Missing heartbeat from source {zombie_source}, dead?")
        self.assertEqual(timestamp, incident.start_time)
        tags = [tag.representation for tag in incident.deprecated_tags]
        expected_tags = [HEARTBEAT_TAG, f"{SOURCE_TAG_KEY}={zombie_source.name}"]
        self.assertEqual(set(tags), set(expected_tags))

    def test_when_source_is_dead_and_timestamp_not_set_incident_generates_a_timestamp(self):
        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)
        self.assertEqual(in_timestamp, timestamp)
        incident = _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        self.assertNotEqual(in_timestamp, incident.start_time)

    def test_when_dead_sources_exist_we_only_make_one_incident_per_source(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().exists())

        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)
        incident1 = _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        incident2 = _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        self.assertEqual(incident1.pk, incident2.pk)


class TestCreateIncidentsForDeadSources(MakeImmutableFixtures, TestCase):
    def test_when_no_dead_sources_returns_empty_list(self):
        incidents = _create_incidents_for_dead_sources(tznow())
        self.assertFalse(incidents)

    def test_when_dead_sources_exist_return_list_of_incidents(self):
        zombie_source, timestamp = create_dead_source("zombie_walking")
        incidents = _create_incidents_for_dead_sources(timestamp)
        self.assertTrue(incidents)
        tags = [tag.representation for tag in incidents[0].deprecated_tags]
        self.assertIn(HEARTBEAT_TAG, tags)
        self.assertIn(f"{SOURCE_TAG_KEY}={zombie_source.name}", tags)


class TestCloseIncidentsWhoseSourcesAreAliveAgain(MakeImmutableFixtures, TestCase):
    def test_when_no_reanimated_sources_return_empty_list(self):
        result = _close_incidents_whose_sources_are_alive_again(tznow())
        self.assertFalse(result)

    def test_when_a_reanimated_source_with_heartbeat_incident_exist_close_it(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().open().exists())
        zombie_source, timestamp = create_dead_source("zombie_walking")
        _create_incidents_for_dead_sources(timestamp)
        self.assertTrue(Incident.objects.heartbeat_incidents().open().exists())

        # reawaken source
        zombie_source.last_seen = tznow()
        zombie_source.save()

        result = _close_incidents_whose_sources_are_alive_again(tznow())
        self.assertFalse(Incident.objects.heartbeat_incidents().open().exists())
        self.assertIn(zombie_source, result)


class TestSyncHeartbeatsWithHeartbeatIncidents(MakeImmutableFixtures, TestCase):
    def test_when_no_relevant_incidents_or_sources_return_two_empty_lists(self):
        sources, incidents = sync_heartbeats_with_heartbeat_incidents()
        self.assertEqual(sources, [])
        self.assertEqual(incidents, [])

    def test_when_relevant_incidents_exist_and_source_is_alive_again_return_reanimated_sources(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().exists())
        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)
        _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        # reawaken source
        zombie_source.last_seen = tznow()
        zombie_source.save()

        reanimated_sources, incidents = sync_heartbeats_with_heartbeat_incidents()
        self.assertIn(zombie_source, reanimated_sources)
        self.assertEqual(incidents, [])

    def test_when_relevant_incidents_exist_return_incidents(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().exists())
        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)
        incident = _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        self.assertEqual(Incident.objects.heartbeat_incidents().open().count(), 1)
        reanimated_sources, incidents = sync_heartbeats_with_heartbeat_incidents()
        self.assertEqual(reanimated_sources, [])
        # should not duplicate incident
        self.assertEqual(Incident.objects.heartbeat_incidents().open().count(), 1)
        result_incident = incidents[0]
        self.assertEqual(incident.pk, result_incident.pk)
        self.assertEqual(incident.description, result_incident.description)
