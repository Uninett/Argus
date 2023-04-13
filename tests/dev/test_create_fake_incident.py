from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from argus.incident.models import Incident, Tag
from argus.util.testing import connect_signals, disconnect_signals


class CreateFakeIncidentTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "create_fake_incident",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_create_fake_incident_will_create_single_fake_incident(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        out = self.call_command()

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .exists()
        )

    def test_create_fake_incident_will_create_multiple_fake_incidents(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        out = self.call_command("--batch-size=5")

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertEqual(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .count(),
            5,
        )

    def test_create_fake_incident_will_create_single_fake_incident_with_set_description(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        description = "Specific description"
        out = self.call_command(f"--description={description}")

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(description=description)
            .exists()
        )

    def test_create_fake_incident_will_create_single_fake_incident_with_set_level(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        level = 2
        out = self.call_command(f"--level={level}")

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(level=level)
            .exists()
        )

    def test_create_fake_incident_will_raise_error_for_invalid_level(self):
        with self.assertRaises(CommandError):
            self.call_command(f"--level=100")

    def test_create_fake_incident_will_create_single_fake_incident_with_set_tag(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        tag_key = "a"
        tag_value = "b"
        out = self.call_command(f"--tags={tag_key}={tag_value}")

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        added_tag = Tag.objects.get(key=tag_key, value=tag_value)
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(incident_tag_relations__tag=added_tag)
            .exists()
        )

    def test_create_fake_incident_will_create_single_fake_stateless_incident(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        out = self.call_command(f"--stateless")

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.stateless()
            .exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .exists()
        )
