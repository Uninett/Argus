import json
from io import StringIO

from django.core.files.temp import NamedTemporaryFile
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils.dateparse import parse_datetime

from argus.incident.models import Incident, SourceSystem, Tag, get_or_create_default_instances
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

    def test_create_fake_incident_will_create_single_fake_incident_with_set_source(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        source_name = "notargus"

        out = self.call_command(f"--source={source_name}")

        self.assertFalse(out)

        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks).filter(source__name=source_name).exists()
        )

    def test_create_fake_incident_will_create_source_if_not_existing(self):
        source_name = "source_a"

        out = self.call_command(f"--source={source_name}")

        self.assertFalse(out)

        source = SourceSystem.objects.filter(name=source_name).first()
        self.assertTrue(source)
        self.assertEqual(source.type_id, source_name)

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
            self.call_command("--level=100")

    def test_create_fake_incident_will_create_single_fake_incident_with_set_tag(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        tag_key = "a"
        tag_value = "b"
        out = self.call_command(f"--tags={tag_key}={tag_value}")

        self.assertFalse(out)

        added_tag = Tag.objects.get(key=tag_key, value=tag_value)
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=added_tag)
            .exists()
        )

    def test_create_fake_incident_will_create_single_fake_stateless_incident(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        out = self.call_command("--stateless")

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.stateless()
            .exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .exists()
        )

    def test_create_fake_incident_will_create_single_fake_incident_with_set_metadata(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        metadata = '{"a":"b"}'
        out = self.call_command(f"--metadata={metadata}")

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(metadata=json.loads(metadata))
            .exists()
        )

    def test_create_fake_incident_will_create_single_fake_incident_with_set_metadata_from_file(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        metadata = b'{"a": "b"}'
        metadata_file = NamedTemporaryFile(delete=True)
        metadata_file.write(metadata)
        metadata_file.flush()
        out = self.call_command(f"--metadata-file={metadata_file.name}")

        self.assertFalse(out)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(metadata=json.loads(metadata))
            .exists()
        )

    def test_create_fake_incident_will_raise_error_for_non_existent_metadata_file(self):
        with self.assertRaises(CommandError):
            self.call_command("--metadata-file=invalid")

    def test_create_fake_incident_will_raise_error_for_extra_arguments_to_file(self):
        incident_data = {
            "start_time": "2025-05-14T11:14:41.391Z",
            "end_time": "2025-05-16T11:14:41.391Z",
            "source_incident_id": "1234",
            "details_url": "nav.example.com/event/1131",
            "description": "Box down router.lab.example.com",
            "level": 2,
            "tags": [{"location": "Teknobyen", "customer": "Sikt"}],
        }

        data = json.dumps(incident_data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()

        with self.assertRaises(CommandError):
            self.call_command(f"--file={file.name}", "--level=3")

    def test_create_fake_incident_will_raise_error_for_non_existent_file(self):
        with self.assertRaises(CommandError):
            self.call_command("--file=invalid")

    def test_create_fake_incident_will_create_single_fake_incident_with_set_data_from_file(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        incident_data = {
            "start_time": "2025-05-14T11:14:41.391Z",
            "end_time": "2025-05-16T11:14:41.391Z",
            "source_incident_id": "1234",
            "source": "abc",
            "details_url": "nav.example.com/event/1131",
            "description": "Box down router.lab.example.com",
            "level": 2,
            "ticket_url": "https://www.example.com/ticket/11234",
            "tags": ["location=Teknobyen", "customer=Sikt"],
        }

        data = json.dumps(incident_data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()
        out = self.call_command(f"--file={file.name}")

        self.assertFalse(out)

        incident = (
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(source_incident_id=incident_data["source_incident_id"])
            .first()
        )

        self.assertTrue(incident)
        self.assertEqual(incident.start_time, parse_datetime(incident_data["start_time"]))
        self.assertEqual(incident.end_time, parse_datetime(incident_data["end_time"]))
        self.assertEqual(incident.source.name, incident_data["source"])
        self.assertEqual(incident.details_url, incident_data["details_url"])
        self.assertEqual(incident.description, incident_data["description"])
        self.assertEqual(incident.level, incident_data["level"])
        self.assertEqual(incident.ticket_url, incident_data["ticket_url"])

    def test_create_fake_incident_will_use_argus_source_if_none_specified(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        incident_data = {"source_incident_id": "1234"}

        data = json.dumps(incident_data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()
        out = self.call_command(f"--file={file.name}")

        self.assertFalse(out)

        incident = (
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(source_incident_id=incident_data["source_incident_id"])
            .first()
        )

        _, _, argus_source_system = get_or_create_default_instances()

        self.assertTrue(incident)
        self.assertEqual(incident.source, argus_source_system)

    def test_create_fake_incident_will_silently_fail_on_invalid_data_from_file(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        incident_data = {
            "source_incident_id": "1234",
            "ticket_url": "invalid-url",
        }

        data = json.dumps(incident_data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()
        out = self.call_command(f"--file={file.name}")

        self.assertFalse(out)

        self.assertFalse(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(source_incident_id=incident_data["source_incident_id"])
            .exists()
        )
