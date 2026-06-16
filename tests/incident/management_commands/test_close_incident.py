from datetime import timedelta
from unittest.mock import patch
import json

from django.core.files.temp import NamedTemporaryFile
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from argus.incident.factories import StatefulIncidentFactory, StatelessIncidentFactory
from argus.incident.models import Event, Incident, get_or_create_default_instances
from argus.util.testing import connect_signals, disconnect_signals


class CloseIncidentArgumentsTests(TestCase):
    def setUp(self):
        disconnect_signals()
        _, _, self.argus_source_system = get_or_create_default_instances()

    def tearDown(self):
        connect_signals()

    def test_closes_incident_using_id(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        call_command("close_incident", id=incident.id)

        incident.refresh_from_db()

        self.assertFalse(incident.open)
        self.assertTrue(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_closes_incident_using_source_and_source_incident_id(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        call_command("close_incident", source=incident.source.name, source_incident_id=incident.source_incident_id)

        incident.refresh_from_db()

        self.assertFalse(incident.open)
        self.assertTrue(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_does_not_close_stateless_incident(self):
        incident = StatelessIncidentFactory(source=self.argus_source_system)

        call_command("close_incident", id=incident.id)

        incident.refresh_from_db()

        self.assertFalse(incident.stateful)
        self.assertFalse(incident.open)
        self.assertFalse(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_closes_incident_older_than_duration(self):
        incident = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(days=10), source=self.argus_source_system
        )

        call_command("close_incident", id=incident.id, duration="00:01:00")

        incident.refresh_from_db()

        self.assertFalse(incident.open)
        self.assertTrue(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_does_not_close_incident_younger_than_duration(self):
        incident = StatefulIncidentFactory(start_time=timezone.now(), source=self.argus_source_system)

        call_command("close_incident", id=incident.id, duration="20:00:00")

        incident.refresh_from_db()

        self.assertTrue(incident.open)
        self.assertFalse(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_closes_incident_with_set_closing_message(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)
        closing_message = "Box back up"

        call_command("close_incident", id=incident.id, closing_message=closing_message)

        incident.refresh_from_db()

        self.assertFalse(incident.open)

        closing_event = incident.events.filter(type=Event.Type.CLOSE).first()
        self.assertEqual(closing_event.description, closing_message)

    def test_does_not_fail_on_non_existent_incident_using_id(self):
        last_incident_pk = Incident.objects.last().id if Incident.objects.exists() else 0
        call_command("close_incident", id=last_incident_pk + 1)

    def test_does_not_fail_on_non_existent_incident_using_source_and_source_incident_id(self):
        call_command("close_incident", source="non-existent", source_incident_id=11111145)

    def test_does_not_close_incident_on_badly_formatted_duration(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        call_command("close_incident", id=incident.id, duration="invalid-format")

        incident.refresh_from_db()

        self.assertTrue(incident.open)
        self.assertFalse(incident.events.filter(type=Event.Type.CLOSE).exists())

    @patch("django.utils.dateparse.parse_duration", side_effect=ValueError)
    def test_does_not_close_incident_on_invalid_duration(self, mock_parse_duration):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        call_command("close_incident", id=incident.id, duration="invalid-format")

        incident.refresh_from_db()

        self.assertTrue(incident.open)
        self.assertFalse(incident.events.filter(type=Event.Type.CLOSE).exists())


class CloseIncidentFilesTests(TestCase):
    def setUp(self):
        disconnect_signals()
        _, _, self.argus_source_system = get_or_create_default_instances()

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

    def test_closes_incident_with_set_id(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        incident_data = {"id": incident.id}

        file = self.create_file(incident_data)
        call_command("close_incident", files=[file.name])

        incident.refresh_from_db()

        self.assertFalse(incident.open)
        self.assertTrue(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_closes_incident_with_set_source_and_source_incident_id(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        incident_data = {"source": self.argus_source_system.name, "source_incident_id": incident.source_incident_id}

        file = self.create_file(incident_data)
        call_command("close_incident", files=[file.name])

        incident.refresh_from_db()

        self.assertFalse(incident.open)
        self.assertTrue(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_closes_incidents_with_one_set_id_and_one_source_and_source_incident_id(self):
        incident_1 = StatefulIncidentFactory(source=self.argus_source_system)
        incident_2 = StatefulIncidentFactory(source=self.argus_source_system)

        incident_data_1 = {"id": incident_1.id}
        file_1 = self.create_file(incident_data_1)
        incident_data_2 = {"source": incident_2.source.name, "source_incident_id": incident_2.source_incident_id}
        file_2 = self.create_file(incident_data_2)

        call_command("close_incident", files=[file_1.name, file_2.name])

        incident_1.refresh_from_db()
        incident_2.refresh_from_db()

        self.assertFalse(incident_1.open)
        self.assertTrue(incident_1.events.filter(type=Event.Type.CLOSE).exists())
        self.assertFalse(incident_2.open)
        self.assertTrue(incident_2.events.filter(type=Event.Type.CLOSE).exists())

    def test_raises_error_for_additional_arguments_to_files(self):
        with self.assertRaises(CommandError):
            call_command("close_incident", files=["file-name"], id=1111)

    def test_does_not_raise_error_for_non_existent_file(self):
        call_command("close_incident", files=["invalid"])

    def test_closes_incident_with_longer_duration(self):
        incident = StatefulIncidentFactory(
            start_time=timezone.now() - timedelta(days=10), source=self.argus_source_system
        )

        incident_data = {"id": incident.id, "duration": "00:01:00"}

        file = self.create_file(incident_data)
        call_command("close_incident", files=[file.name])

        incident.refresh_from_db()

        self.assertFalse(incident.open)
        self.assertTrue(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_does_not_close_incident_with_shorter_duration(self):
        incident = StatefulIncidentFactory(start_time=timezone.now(), source=self.argus_source_system)

        incident_data = {"id": incident.id, "duration": "20:00:00"}

        file = self.create_file(incident_data)
        call_command("close_incident", files=[file.name])

        incident.refresh_from_db()

        self.assertTrue(incident.open)
        self.assertFalse(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_does_not_close_incident_on_badly_formatted_duration(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        incident_data = {"id": incident.id, "duration": "invalid-format"}

        file = self.create_file(incident_data)

        call_command("close_incident", files=[file.name])

        incident.refresh_from_db()

        self.assertTrue(incident.open)
        self.assertFalse(incident.events.filter(type=Event.Type.CLOSE).exists())

    @patch("django.utils.dateparse.parse_duration", side_effect=ValueError)
    def test_does_not_close_incident_on_invalid_duration(self, mock_parse_duration):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        incident_data = {"id": incident.id, "duration": "invalid-format"}

        file = self.create_file(incident_data)

        call_command("close_incident", files=[file.name])

        incident.refresh_from_db()

        self.assertTrue(incident.open)
        self.assertFalse(incident.events.filter(type=Event.Type.CLOSE).exists())

    def test_closes_incident_with_closing_message(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)
        closing_message = "Box back up"

        incident_data = {"id": incident.id, "closing_message": closing_message}

        file = self.create_file(incident_data)
        call_command("close_incident", files=[file.name])

        incident.refresh_from_db()

        self.assertFalse(incident.open)

        closing_event = incident.events.filter(type=Event.Type.CLOSE).first()
        self.assertEqual(closing_event.description, closing_message)

    def test_does_not_fail_on_non_existent_incident_using_id(self):
        last_incident_pk = Incident.objects.last().id if Incident.objects.exists() else 0

        incident_data = {"id": last_incident_pk + 1}

        file = self.create_file(incident_data)
        call_command("close_incident", files=[file.name])

    def test_does_not_fail_on_non_existent_incident_using_source_and_source_incident_id(self):
        incident_data = {"source": "non-existent", "source_incident_id": 11111145}

        file = self.create_file(incident_data)
        call_command("close_incident", files=[file.name])

    def test_ignores_extra_data(self):
        incident = StatefulIncidentFactory(source=self.argus_source_system)

        incident_data = {"id": incident.id, "extra_info": "abc"}

        file = self.create_file(incident_data)
        call_command("close_incident", files=[file.name])

        incident.refresh_from_db()

        self.assertFalse(incident.open)
        self.assertTrue(incident.events.filter(type=Event.Type.CLOSE).exists())
