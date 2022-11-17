from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.test import TestCase

from argus.incident.factories import StatefulIncidentFactory
from argus.incident.ticket.dummy import created_tickets
from argus.util.utils import import_class_from_dotted_path
from argus.util.testing import disconnect_signals, connect_signals


class DummyTicketSystemTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_create_ticket_writes_to_local_variable(self):
        dummy_class = import_class_from_dotted_path("argus.incident.ticket.dummy.DummyPlugin")

        incident = StatefulIncidentFactory()

        ticket_data = {
            "title": str(incident),
            "description": incident.description,
        }

        url = dummy_class.create_ticket(incident)

        url_validator = URLValidator()

        try:
            url_validator(url)
        except ValidationError as e:
            self.fail(f"Invalid url: {url}, details: {e}")

        self.assertIn(ticket_data, list(map(lambda x: x[0], created_tickets)))
