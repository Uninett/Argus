from django.test import TestCase, tag

from argus.auth.factories import AdminUserFactory, SourceUserFactory
from argus.incident.factories import (
    EventFactory,
    IncidentTagRelationFactory,
    SourceSystemFactory,
    SourceSystemTypeFactory,
    StatefulIncidentFactory,
    StatelessIncidentFactory,
    TagFactory,
)
from argus.incident.models import Incident, Event
from argus.filter.queryset_filters import (
    QuerySetFilter,
    _incidents_fitting_event_types,
    _incidents_fitting_maxlevel,
    _incidents_fitting_tristates,
    _incidents_with_source_system_types,
    _incidents_with_source_systems,
    _incidents_with_tags,
)
from argus.util.testing import disconnect_signals, connect_signals


@tag("database", "queryset-filter")
class FilteredIncidentsHelpersTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source_type1 = SourceSystemTypeFactory(name="type1")
        cls.source1_user = SourceUserFactory(username="system_1")
        cls.source1 = SourceSystemFactory(name="System 1", type=cls.source_type1, user=cls.source1_user)

        cls.user1 = AdminUserFactory(username="user1")

        cls.source_type2 = SourceSystemTypeFactory(name="type2")
        cls.source2_user = SourceUserFactory(username="system_2")
        cls.source2 = SourceSystemFactory(name="System 2", type=cls.source_type2, user=cls.source2_user)

        cls.incident1 = StatelessIncidentFactory(source=cls.source1)
        EventFactory(incident=cls.incident1, type=Event.Type.STATELESS)
        cls.incident2 = StatelessIncidentFactory(source=cls.source2)
        EventFactory(incident=cls.incident2, type=Event.Type.STATELESS)

        cls.tag1 = TagFactory(key="object", value="1")
        cls.tag2 = TagFactory(key="object", value="2")
        cls.tag3 = TagFactory(key="location", value="Oslo")

        IncidentTagRelationFactory(tag=cls.tag1, incident=cls.incident1, added_by=cls.user1)
        IncidentTagRelationFactory(tag=cls.tag3, incident=cls.incident1, added_by=cls.user1)
        IncidentTagRelationFactory(tag=cls.tag2, incident=cls.incident2, added_by=cls.user1)
        IncidentTagRelationFactory(tag=cls.tag3, incident=cls.incident2, added_by=cls.user1)

    def setUp(self):
        disconnect_signals()
        self.all_incidents = Incident.objects.all()

    def teardown(self):
        connect_signals()

    def test_incidents_with_source_systems_empty_if_no_incidents_with_these_source_systems(self):
        source_user3 = SourceUserFactory()
        source3 = SourceSystemFactory(user=source_user3)
        self.assertFalse(_incidents_with_source_systems(self.all_incidents, {"sourceSystemIds": [source3.pk]}))

    def test_incidents_with_source_systems_finds_incidents_with_these_source_systems(self):
        source1_filtered_incidents = list(
            _incidents_with_source_systems(self.all_incidents, {"sourceSystemIds": [self.source1.pk]})
        )
        self.assertIn(self.incident1, source1_filtered_incidents)
        self.assertNotIn(self.incident2, source1_filtered_incidents)

    def test_incidents_with_source_system_type_empty_if_no_incidents_with_these_source_system_types(self):
        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        self.assertFalse(_incidents_with_source_system_types(self.all_incidents, {"source_types": [source.type]}))

    def test_incidents_with_source_system_types_finds_incidents_with_these_source_system_types(self):
        source1_filtered_incidents = list(
            _incidents_with_source_system_types(self.all_incidents, {"source_types": [self.source1.type]})
        )
        self.assertIn(self.incident1, source1_filtered_incidents)
        self.assertNotIn(self.incident2, source1_filtered_incidents)

    def test_incidents_with_event_type_empty_if_no_incidents_with_these_event_types(self):
        event_type = Event.Type.OTHER
        self.assertFalse(_incidents_fitting_event_types(self.all_incidents, {"event_types": [event_type]}))

    def test_incidents_fitting_event_types_finds_incidents_fitting_these_event_types(self):
        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        incident = StatefulIncidentFactory(source=source)
        EventFactory(incident=incident, type=Event.Type.INCIDENT_START)
        all_incidents = Incident.objects.all()
        filtered_incidents = list(
            _incidents_fitting_event_types(all_incidents, {"event_types": [Event.Type.INCIDENT_START]})
        )
        self.assertIn(incident, filtered_incidents)
        self.assertNotIn(self.incident2, filtered_incidents)

    def test_incidents_with_tags_empty_if_no_incidents_with_these_tags(self):
        tag4 = TagFactory()
        self.assertFalse(_incidents_with_tags(self.all_incidents, {"tags": [str(tag4)]}))

    def test_incidents_with_tags_finds_incidents_with_these_tags(self):
        tags1_filtered_incidents = list(_incidents_with_tags(self.all_incidents, {"tags": [str(self.tag1)]}))
        self.assertIn(self.incident1, tags1_filtered_incidents)
        self.assertNotIn(self.incident2, tags1_filtered_incidents)

    def test_incidents_fitting_tristates_empty_if_no_incidents_with_these_tristates(self):
        self.assertFalse(_incidents_fitting_tristates(self.all_incidents, {"stateful": True}))

    def test_incidents_fitting_tristates_finds_incidents_with_these_tristates(self):
        stateless_filtered_incidents = list(_incidents_fitting_tristates(self.all_incidents, {"stateful": False}))
        self.assertIn(self.incident1, stateless_filtered_incidents)
        self.assertIn(self.incident2, stateless_filtered_incidents)

    def test_incidents_fitting_maxlevel_empty_if_no_incidents_with_this_maxlevel(self):
        self.incident1.level = 5
        self.incident1.save(update_fields=["level"])
        self.incident2.level = 5
        self.incident2.save(update_fields=["level"])

        self.assertFalse(_incidents_fitting_maxlevel(self.all_incidents, {"maxlevel": 1}))

    def test_incidents_fitting_maxlevel_finds_incidents_with_this_maxlevel(self):
        maxlevel_filtered_incidents = list(_incidents_fitting_maxlevel(self.all_incidents, {"maxlevel": 5}))
        self.assertIn(self.incident1, maxlevel_filtered_incidents)
        self.assertIn(self.incident2, maxlevel_filtered_incidents)


@tag("database", "queryset-filter")
class FilteredIncidentsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source_type1 = SourceSystemTypeFactory(name="type1")
        cls.source1_user = SourceUserFactory(username="system_1")
        cls.source1 = SourceSystemFactory(name="System 1", type=cls.source_type1, user=cls.source1_user)

        cls.user1 = AdminUserFactory(username="user1")

        cls.source_type2 = SourceSystemTypeFactory(name="type2")
        cls.source2_user = SourceUserFactory(username="system_2")
        cls.source2 = SourceSystemFactory(name="System 2", type=cls.source_type2, user=cls.source2_user)

        cls.incident1 = StatelessIncidentFactory(source=cls.source1)
        cls.incident2 = StatelessIncidentFactory(source=cls.source2)

        cls.tag1 = TagFactory(key="object", value="1")
        cls.tag2 = TagFactory(key="object", value="2")
        cls.tag3 = TagFactory(key="location", value="Oslo")

        IncidentTagRelationFactory(tag=cls.tag1, incident=cls.incident1, added_by=cls.user1)
        IncidentTagRelationFactory(tag=cls.tag3, incident=cls.incident1, added_by=cls.user1)
        IncidentTagRelationFactory(tag=cls.tag2, incident=cls.incident2, added_by=cls.user1)
        IncidentTagRelationFactory(tag=cls.tag3, incident=cls.incident2, added_by=cls.user1)

    def setUp(self):
        disconnect_signals()

    def teardown(self):
        connect_signals()

    def test_filtered_incidents_returns_empty_if_no_incident_fits_filter(self):
        self.assertEqual(set(QuerySetFilter.filtered_incidents(dict())), set())

    def test_filtered_incidents_returns_incident_if_incident_fits_filter(self):
        self.assertEqual(
            set(QuerySetFilter.filtered_incidents({"sourceSystemIds": [self.source1.pk]})), {self.incident1}
        )
        self.assertEqual(
            set(QuerySetFilter.filtered_incidents({"sourceSystemIds": [self.source2.pk]})), {self.incident2}
        )

        self.assertEqual(set(QuerySetFilter.filtered_incidents({"tags": [str(self.tag1)]})), {self.incident1})
        self.assertEqual(set(QuerySetFilter.filtered_incidents({"tags": [str(self.tag2)]})), {self.incident2})

        self.assertEqual(
            set(QuerySetFilter.filtered_incidents({"sourceSystemIds": [self.source1.pk], "tags": [str(self.tag1)]})),
            {self.incident1},
        )
