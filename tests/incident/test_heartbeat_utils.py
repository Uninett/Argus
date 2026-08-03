from datetime import timedelta

from django.test import TestCase, tag
from django.utils.timezone import now as tznow

from argus.incident.factories import SourceSystemFactory, create_dead_source, create_fake_incident
from argus.incident.heartbeat_utils import (
    HEARTBEAT_TAG,
    SOURCE_TAG_KEY,
    _close_heartbeat_incidents,
    _create_incidents_for_dead_sources,
    _get_or_create_incident_for_dead_source,
    sync_heartbeats_with_heartbeat_incidents,
)
from argus.incident.models import Incident, Tag, get_or_create_default_instances


class MakeImmutableFixtures:
    def setUp(self):
        _, sst, self.owner_source = get_or_create_default_instances()
        self.alive_source = SourceSystemFactory(
            name="spring_blossom", last_seen=tznow(), heartbeat_frequency=timedelta(days=1)
        )
        self.irrelevant_incident = create_fake_incident(source=self.owner_source.name, tags=["test=test"])


class TestGetOrCreateIncidentForDeadSource(MakeImmutableFixtures, TestCase):
    def test_when_source_is_not_dead_we_create_nothing(self):
        incident, new = _get_or_create_incident_for_dead_source(
            self.alive_source, incident_owner=self.owner_source, timestamp=self.alive_source.last_seen
        )
        self.assertIsNone(incident)
        self.assertIsNone(new)

    def test_when_source_is_dead_then_created_incident_has_correct_description_and_tags(self):
        zombie_source, timestamp = create_dead_source("zombie_walking")
        incident, new = _get_or_create_incident_for_dead_source(
            zombie_source, incident_owner=self.owner_source, timestamp=timestamp
        )
        self.assertTrue(new)
        self.assertEqual(incident.description, f"Missing heartbeat from source {zombie_source}, dead?")
        self.assertEqual(timestamp, incident.start_time)
        tags = [tag.representation for tag in incident.deprecated_tags]
        expected_tags = [HEARTBEAT_TAG, f"{SOURCE_TAG_KEY}={zombie_source.pk}"]
        self.assertEqual(set(tags), set(expected_tags))

    def test_when_source_is_dead_and_timestamp_not_set_incident_generates_a_timestamp(self):
        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)
        self.assertEqual(in_timestamp, timestamp)
        incident, _ = _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        self.assertNotEqual(in_timestamp, incident.start_time)

    def test_when_incident_for_dead_source_exist_then_do_not_create_new_incident(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().exists())

        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)
        incident1, new1 = _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        incident2, new2 = _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        self.assertTrue(new1)
        self.assertFalse(new2)
        self.assertEqual(incident1.pk, incident2.pk)


class TestCreateIncidentsForDeadSources(MakeImmutableFixtures, TestCase):
    def test_when_no_dead_sources_returns_tuple_of_two_empty_lists(self):
        new_incidents, existing_incidents = _create_incidents_for_dead_sources(tznow())
        self.assertFalse(new_incidents)
        self.assertFalse(existing_incidents)

    def test_when_dead_sources_exist_return_list_of_created_incidents_and_an_empty_list(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().open().exists())
        zombie_source, timestamp = create_dead_source("zombie_walking")
        new_incidents, existing_incidents = _create_incidents_for_dead_sources(timestamp)
        self.assertTrue(Incident.objects.heartbeat_incidents().open().exists())
        self.assertTrue(new_incidents)
        self.assertFalse(existing_incidents)
        tags = [tag.representation for tag in new_incidents[0].deprecated_tags]
        self.assertIn(HEARTBEAT_TAG, tags)
        self.assertIn(f"{SOURCE_TAG_KEY}={zombie_source.pk}", tags)


@tag("db")
class TestCloseHeartbeatIncidents(MakeImmutableFixtures, TestCase):
    @staticmethod
    def _create_dead_source_and_incident():
        zombie_source, timestamp = create_dead_source("zombie_walking")
        new_incidents, existing_incidents = _create_incidents_for_dead_sources(timestamp)
        return zombie_source, new_incidents, existing_incidents

    def test_when_no_reanimated_sources_return_empty_lists(self):
        sources, closed_incidents, remaining_incidents = _close_heartbeat_incidents(tznow())
        self.assertFalse(sources)
        self.assertFalse(closed_incidents)
        self.assertFalse(remaining_incidents)

    def test_when_a_reanimated_source_with_heartbeat_incident_exists_then_close_incident(self):
        zombie_source, new_incidents, existing_incidents = self._create_dead_source_and_incident()
        self.assertFalse(existing_incidents)

        # reawaken source
        zombie_source.last_seen = tznow()
        zombie_source.save()

        incident = new_incidents[0]
        sources, closed_incidents, remaining_incidents = _close_heartbeat_incidents(tznow())
        self.assertFalse(Incident.objects.heartbeat_incidents().open().exists())
        self.assertIn(zombie_source, sources)
        self.assertIn(incident, closed_incidents)
        self.assertFalse(remaining_incidents)

    def test_when_a_heartbeat_incident_lacks_the_sourcetag_close_it(self):
        zombie_source, new_incidents, _ = self._create_dead_source_and_incident()

        # remove source tag
        tags = Tag.objects.filter(key=SOURCE_TAG_KEY)
        incident = new_incidents[0]
        incident.incident_tag_relations.filter(tag__in=tags).delete()
        incident.refresh_from_db()
        self.assertFalse(Incident.objects.heartbeat_incidents().from_tag_keys(tags[0].representation).open().exists())

        # reawaken source
        zombie_source.last_seen = tznow()
        zombie_source.save()

        sources, closed_incidents, remaining_incidents = _close_heartbeat_incidents(tznow())

        # incidents without source tags are just closed regardless
        self.assertFalse(Incident.objects.heartbeat_incidents().open().exists())
        self.assertNotIn(zombie_source, sources)
        self.assertIn(incident, closed_incidents)
        self.assertEqual(remaining_incidents, [])

    def test_when_a_heartbeat_incident_has_multiple_sourcetags_leave_it_alone(self):
        zombie_source, new_incidents, _ = self._create_dead_source_and_incident()
        incident = new_incidents[0]
        self.assertEqual(len(incident.deprecated_tags), 2)

        additional_tag = Tag.objects.create(key=SOURCE_TAG_KEY, value=str(2**32 - 1))
        incident.incident_tag_relations.create(added_by=zombie_source.user, tag=additional_tag)
        incident.refresh_from_db()
        self.assertEqual(len(incident.deprecated_tags), 3)

        # reawaken source
        zombie_source.last_seen = tznow()
        zombie_source.save()

        sources, closed_incidents, remaining_incidents = _close_heartbeat_incidents(tznow())
        # not found, so not closed!
        self.assertTrue(Incident.objects.heartbeat_incidents().open().exists())
        self.assertNotIn(zombie_source, sources)
        self.assertEqual(closed_incidents, [])
        self.assertIn(incident, remaining_incidents)

    def test_close_all_incidents_pointing_to_a_nonexistent_source(self):
        zombie_source, new_incidents, _ = self._create_dead_source_and_incident()
        incident = new_incidents[0]
        self.assertEqual(len(incident.deprecated_tags), 2)

        zombie_source.delete()

        sources, closed_incidents, remaining_incidents = _close_heartbeat_incidents(tznow())
        # source not found, so closed!
        self.assertFalse(Incident.objects.heartbeat_incidents().open().exists())
        self.assertNotIn(zombie_source, sources)
        self.assertIn(incident, closed_incidents)
        self.assertEqual(remaining_incidents, [])


class TestSyncHeartbeatsWithHeartbeatIncidents(MakeImmutableFixtures, TestCase):
    def test_when_no_relevant_incidents_or_sources_return_two_empty_lists(self):
        sources, new_incidents, remaining_incidents = sync_heartbeats_with_heartbeat_incidents()
        self.assertEqual(sources, [])
        self.assertEqual(new_incidents, [])
        self.assertEqual(remaining_incidents, [])

    def test_when_relevant_incidents_exist_return_them(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().exists())
        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)

        # Get or create heartbeat incident inside the sync
        sources, new_incidents, remaining_incidents = sync_heartbeats_with_heartbeat_incidents()
        self.assertEqual(Incident.objects.heartbeat_incidents().open().count(), 1)
        self.assertEqual(sources, [])
        self.assertTrue(new_incidents)
        self.assertEqual(remaining_incidents, [])

    def test_when_relevant_incidents_exist_return_incident_without_duplications(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().exists())
        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)

        # Get or create heartbeat incident outside of the sync
        incident, _ = _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        self.assertEqual(Incident.objects.heartbeat_incidents().open().count(), 1)

        # Get or create heartbeat incident inside the sync, without dupliaction
        sources, new_incidents, remaining_incidents = sync_heartbeats_with_heartbeat_incidents()
        self.assertEqual(Incident.objects.heartbeat_incidents().open().count(), 1)
        self.assertEqual(sources, [])
        self.assertEqual(new_incidents, [])
        self.assertTrue(remaining_incidents)

        # should not duplicate incident
        result_incident = remaining_incidents[0]
        self.assertEqual(incident.pk, result_incident.pk)
        self.assertEqual(incident.description, result_incident.description)

    def test_when_relevant_incidents_exist_and_source_is_alive_again_return_reanimated_sources(self):
        self.assertFalse(Incident.objects.heartbeat_incidents().exists())
        in_timestamp = tznow() - timedelta(seconds=60)
        zombie_source, timestamp = create_dead_source("zombie_walking", timestamp=in_timestamp)
        _get_or_create_incident_for_dead_source(zombie_source, incident_owner=self.owner_source)
        # reawaken source
        zombie_source.last_seen = tznow()
        zombie_source.save()

        sources, new_incidents, remaining_incidents = sync_heartbeats_with_heartbeat_incidents()
        self.assertIn(zombie_source, sources)
        self.assertEqual(new_incidents, [])
        self.assertEqual(remaining_incidents, [])
