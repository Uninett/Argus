from django.test import TestCase


from argus.incident.models import IncidentTagRelation, create_fake_incident
from argus.util.testing import disconnect_signals, connect_signals


class EventViewSetTestCase(TestCase):
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
