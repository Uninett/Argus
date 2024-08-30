from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.test import TestCase

from argus.incident.factories import SourceSystemFactory, SourceUserFactory, StatefulIncidentFactory
from argus.incident.ticket.dummy import created_tickets
from argus.incident.V1.serializers import IncidentSerializerV1
from argus.util.utils import import_class_from_dotted_path
from argus.util.testing import disconnect_signals, connect_signals


class DummyTicketSystemTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_create_ticket_writes_to_local_variable(self):
        dummy_class = import_class_from_dotted_path("argus.incident.ticket.dummy.DummyPlugin")

        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        incident = StatefulIncidentFactory(source=source)

        ticket_data = {
            "title": incident.description,
            "description": incident.description,
        }

        serialized_incident = IncidentSerializerV1(incident).data

        url = dummy_class.create_ticket(serialized_incident)

        url_validator = URLValidator()

        try:
            url_validator(url)
        except ValidationError as e:
            self.fail(f"Invalid url: {url}, details: {e}")

        self.assertIn(ticket_data, list(map(lambda x: x[0], created_tickets)))
