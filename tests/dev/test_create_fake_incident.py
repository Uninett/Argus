import json
from io import StringIO

from django.core.files.temp import NamedTemporaryFile
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils.dateparse import parse_datetime

from argus.incident.factories import StatefulIncidentFactory
from argus.incident.models import Incident, SourceSystem, Tag, get_or_create_default_instances
from argus.util.testing import connect_signals, disconnect_signals


class CreateFakeIncidentWithArgumentsTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        call_command(
            "create_fake_incident",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    def test_creates_single_fake_incident(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        out, err = self.call_command()

        self.assertFalse(out)
        self.assertFalse(err)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .exists()
        )

    def test_creates_multiple_fake_incidents(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        out, err = self.call_command("--batch-size=5")

        self.assertFalse(out)
        self.assertFalse(err)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertEqual(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .count(),
            5,
        )

    def test_creates_single_fake_incident_with_set_description(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        description = "Specific description"
        out, err = self.call_command(f"--description={description}")

        self.assertFalse(out)
        self.assertFalse(err)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(description=description)
            .exists()
        )

    def test_uses_argus_source_if_none_specified(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        out, err = self.call_command()

        self.assertFalse(out)
        self.assertFalse(err)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        incident = (
            Incident.objects.exclude(id__in=previous_incidents_pks).filter(incident_tag_relations__tag=test_tag).first()
        )
        _, _, argus_source_system = get_or_create_default_instances()

        self.assertTrue(incident)
        self.assertEqual(incident.source, argus_source_system)

    def test_creates_single_fake_incident_with_set_source(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        source_name = "notargus"

        out, err = self.call_command(f"--source={source_name}")

        self.assertFalse(out)
        self.assertFalse(err)

        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks).filter(source__name=source_name).exists()
        )

    def test_creates_single_fake_incident_with_set_source_and_source_type(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        source_name = "notargus"
        source_type = "abcd"

        out, err = self.call_command(f"--source={source_name}", f"--source-type={source_type}")

        self.assertFalse(out)
        self.assertFalse(err)

        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(source__name=source_name)
            .filter(source__type__name=source_type)
            .exists()
        )

    def test_creates_source_if_not_existing(self):
        source_name = "source_a"

        out, err = self.call_command(f"--source={source_name}")

        self.assertFalse(out)
        self.assertFalse(err)

        source = SourceSystem.objects.filter(name=source_name).first()
        self.assertTrue(source)
        self.assertEqual(source.type_id, source_name)

    def test_creates_single_fake_incident_with_set_level(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        level = 2
        out, err = self.call_command(f"--level={level}")

        self.assertFalse(out)
        self.assertFalse(err)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(level=level)
            .exists()
        )

    def test_raises_error_for_invalid_level(self):
        with self.assertRaises(CommandError):
            self.call_command("--level=100")

    def test_creates_single_fake_incident_with_set_tag(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        tag_key = "a"
        tag_value = "b"
        out, err = self.call_command(f"--tags={tag_key}={tag_value}")

        self.assertFalse(out)
        self.assertFalse(err)

        added_tag = Tag.objects.get(key=tag_key, value=tag_value)
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=added_tag)
            .exists()
        )

    def test_creates_single_fake_stateless_incident(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        out, err = self.call_command("--stateless")

        self.assertFalse(out)
        self.assertFalse(err)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.stateless()
            .exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .exists()
        )

    def test_creates_single_fake_incident_with_set_metadata(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]
        metadata = '{"a":"b"}'
        out, err = self.call_command(f"--metadata={metadata}")

        self.assertFalse(out)
        self.assertFalse(err)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(metadata=json.loads(metadata))
            .exists()
        )

    def test_creates_single_fake_incident_with_set_metadata_from_file(self):
        previous_incidents_pks = [incident.id for incident in Incident.objects.all()]

        metadata = b'{"a": "b"}'
        metadata_file = NamedTemporaryFile(delete=True)
        metadata_file.write(metadata)
        metadata_file.flush()
        out, err = self.call_command(f"--metadata-file={metadata_file.name}")

        self.assertFalse(out)
        self.assertFalse(err)

        test_tag = Tag.objects.get(key="problem_type", value="test")
        self.assertTrue(
            Incident.objects.exclude(id__in=previous_incidents_pks)
            .filter(incident_tag_relations__tag=test_tag)
            .filter(metadata=json.loads(metadata))
            .exists()
        )

    def test_does_not_create_incident_for_non_existent_metadata_file(self):
        previous_incidents_count = Incident.objects.count()

        out, err = self.call_command("--metadata-file=invalid")

        self.assertFalse(out)
        self.assertIn("Could not find/open/read file", err)

        self.assertEqual(Incident.objects.count(), previous_incidents_count)


class CreateFakeIncidentWithFilesTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    @staticmethod
    def create_file(data: dict) -> str:
        """Creates a NamedTemporaryFile containing the given data and returns it"""

        data = json.dumps(data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()
        return file

    def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        call_command(
            "create_fake_incident",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    def test_raises_error_for_extra_arguments_to_files(self):
        incident_data = {
            "start_time": "2025-05-14T11:14:41.391Z",
            "end_time": "2025-05-16T11:14:41.391Z",
            "source_incident_id": "1234",
            "details_url": "nav.example.com/event/1131",
            "description": "Box down router.lab.example.com",
            "level": 2,
            "tags": [{"location": "Teknobyen", "customer": "Sikt"}],
        }

        file = self.create_file(incident_data)

        with self.assertRaises(CommandError):
            self.call_command(f"--files={file.name}", "--level=3")

    def test_does_not_create_incident_for_non_existent_file(self):
        out, err = self.call_command("--files=invalid")

        self.assertFalse(out)
        self.assertIn("Could not find/open/read file", err)

        self.assertFalse(Incident.objects.exists())

    def test_does_not_create_incident_for_empty_file(self):
        file = NamedTemporaryFile(delete=True)

        out, err = self.call_command(f"--files={file.name}")

        self.assertFalse(out)
        self.assertIn("Could not find/open/read file", err)

        self.assertFalse(Incident.objects.exists())

    def test_creates_single_fake_incident_with_set_data(self):
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
        out, err = self.call_command(f"--files={file.name}")

        self.assertFalse(out)
        self.assertFalse(err)

        incident = Incident.objects.get(source_incident_id=incident_data["source_incident_id"])

        self.assertEqual(incident.start_time, parse_datetime(incident_data["start_time"]))
        self.assertEqual(incident.end_time, parse_datetime(incident_data["end_time"]))
        self.assertEqual(incident.source.name, incident_data["source"])
        self.assertEqual(incident.details_url, incident_data["details_url"])
        self.assertEqual(incident.description, incident_data["description"])
        self.assertEqual(incident.level, incident_data["level"])
        self.assertEqual(incident.ticket_url, incident_data["ticket_url"])

    def test_creates_multiple_fake_incidents_with_set_data(self):
        incident_1_data = {
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
        incident_2_data = {
            "start_time": "2025-05-11T11:14:41.391Z",
            "end_time": "2025-05-19T11:14:41.391Z",
            "source_incident_id": "1235",
            "source": "abc",
            "details_url": "nav.example.com/event/1132",
            "description": "Box down router2.lab.example.com",
            "level": 1,
            "ticket_url": "https://www.example.com/ticket/11235",
            "tags": ["location=Teknobyen", "customer=Sikt"],
        }

        file_1 = self.create_file(incident_1_data)
        file_2 = self.create_file(incident_2_data)

        out, err = self.call_command(files=[file_1.name, file_2.name])

        self.assertFalse(out)
        self.assertFalse(err)

        incident_1 = Incident.objects.get(source_incident_id=incident_1_data["source_incident_id"])
        self.assertEqual(incident_1.start_time, parse_datetime(incident_1_data["start_time"]))
        self.assertEqual(incident_1.end_time, parse_datetime(incident_1_data["end_time"]))
        self.assertEqual(incident_1.source.name, incident_1_data["source"])
        self.assertEqual(incident_1.details_url, incident_1_data["details_url"])
        self.assertEqual(incident_1.description, incident_1_data["description"])
        self.assertEqual(incident_1.level, incident_1_data["level"])
        self.assertEqual(incident_1.ticket_url, incident_1_data["ticket_url"])

        incident_2 = Incident.objects.get(source_incident_id=incident_2_data["source_incident_id"])
        self.assertEqual(incident_2.start_time, parse_datetime(incident_2_data["start_time"]))
        self.assertEqual(incident_2.end_time, parse_datetime(incident_2_data["end_time"]))
        self.assertEqual(incident_2.source.name, incident_2_data["source"])
        self.assertEqual(incident_2.details_url, incident_2_data["details_url"])
        self.assertEqual(incident_2.description, incident_2_data["description"])
        self.assertEqual(incident_2.level, incident_2_data["level"])
        self.assertEqual(incident_2.ticket_url, incident_2_data["ticket_url"])

    def test_uses_argus_source_if_none_specified(self):
        incident_data = {"source_incident_id": "1234"}

        data = json.dumps(incident_data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()
        out, err = self.call_command(f"--files={file.name}")

        self.assertFalse(out)
        self.assertFalse(err)

        incident = Incident.objects.get(source_incident_id=incident_data["source_incident_id"])

        _, _, argus_source_system = get_or_create_default_instances()

        self.assertTrue(incident)
        self.assertEqual(incident.source, argus_source_system)

    def test_does_not_create_incident_for_invalid_data(self):
        incident_data = {
            "source_incident_id": "1234",
            "ticket_url": "invalid-url",
        }

        data = json.dumps(incident_data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()
        out, err = self.call_command(f"--files={file.name}")

        self.assertFalse(out)
        self.assertIn("Enter a valid URL.", err)

        with self.assertRaises(Incident.DoesNotExist):
            Incident.objects.get(source_incident_id=incident_data["source_incident_id"])

    def test_does_not_create_incident_for_same_source_and_source_incident_id_as_existing(self):
        incident = StatefulIncidentFactory()

        incident_data = {
            "source_incident_id": incident.source_incident_id,
            "source": incident.source.name,
            "source_type": incident.source.type.name,
        }

        data = json.dumps(incident_data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()
        out, err = self.call_command(f"--files={file.name}")

        self.assertFalse(out)
        self.assertIn("Source incident ids need to be unique for each source.", err)

        incidents = Incident.objects.filter(
            source_incident_id=incident_data["source_incident_id"],
            source=incident.source,
        )

        self.assertEqual(incidents.count(), 1)

    def test_do_create_another_incident_for_same_source_and_source_incident_id_if_source_incident_id_is_empty_string(
        self,
    ):
        incident = StatefulIncidentFactory(source_incident_id="")

        incident_data = {
            "source_incident_id": incident.source_incident_id,
            "source": incident.source.name,
            "source_type": incident.source.type.name,
        }

        data = json.dumps(incident_data).encode("utf-8")
        file = NamedTemporaryFile(delete=True)
        file.write(data)
        file.flush()
        out, err = self.call_command(f"--files={file.name}")

        self.assertFalse(out)
        self.assertFalse(err)

        incidents = Incident.objects.filter(source_incident_id="")
        self.assertEqual(incidents.count(), 2)
