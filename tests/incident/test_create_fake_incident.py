from django.test import TestCase

from argus.auth.factories import SourceUserFactory
from argus.incident.factories import SourceSystemFactory, SourceSystemTypeFactory
from argus.incident.models import IncidentTagRelation, create_fake_incident
from argus.util.testing import disconnect_signals, connect_signals


class CreateFakeIncidentTestCase(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_create_fake_incident_creates_incident_with_set_tags(self):
        tags = ["a=b", "c=d"]
        incident = create_fake_incident(tags=tags)

        resulting_tags = [str(relation.tag) for relation in IncidentTagRelation.objects.filter(incident=incident)]

        for tag in tags:
            self.assertIn(tag, resulting_tags)

    def test_create_fake_incident_creates_incident_with_set_description(self):
        description = "description"
        incident = create_fake_incident(description=description)

        self.assertEqual(incident.description, description)

    def test_create_fake_incident_creates_stateless_incident(self):
        incident = create_fake_incident(stateful=False)

        self.assertFalse(incident.stateful)

    def test_create_fake_incident_creates_incident_with_set_level(self):
        level = 2
        incident = create_fake_incident(level=level)

        self.assertEqual(incident.level, level)

    def test_create_fake_incident_creates_incident_with_set_existing_source(self):
        source_name = "source_a"
        sst = SourceSystemTypeFactory(name=source_name)
        user = SourceUserFactory(username=source_name)
        SourceSystemFactory(name=source_name, type=sst, user=user)
        incident = create_fake_incident(source=source_name)

        self.assertEqual(incident.source.name, source_name)

    def test_create_fake_incident_raises_error_on_non_existent_source(self):
        with self.assertRaises(ValueError):
            create_fake_incident(source="non-existent")
