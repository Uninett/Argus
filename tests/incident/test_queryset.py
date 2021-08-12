from django.test import TestCase
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.util.testing import disconnect_signals, connect_signals
from argus.incident.factories import IncidentFactory
from argus.incident.models import Incident


class IncidentQuerySetTestCase(TestCase):
    def setUp(self):
        disconnect_signals()
        # Lock in timestamps
        self.timestamp = timezone.now()
        self.incident1 = IncidentFactory(start_time=self.timestamp, end_time=None, ticket_url="")
        self.incident2 = IncidentFactory(start_time=self.timestamp, ticket_url="")
        self.incident3 = IncidentFactory(start_time=self.timestamp, ticket_url="")
        self.incident4 = IncidentFactory(start_time=self.timestamp)
        self.incident4.end_time = self.timestamp
        self.incident4.save()

    def tearDown(self):
        connect_signals()

    def test_stateful(self):
        result = Incident.objects.stateful()
        self.assertNotIn(self.incident1, result)

    def test_stateless(self):
        result = Incident.objects.stateless()
        self.assertEqual(result.get(), self.incident1)

    def test_open(self):
        result = Incident.objects.open()
        self.assertEqual(set(result), set((self.incident2, self.incident3)))

    def test_closed(self):
        result = Incident.objects.closed()
        self.assertEqual(result.get(), self.incident4)

    def test_acked(self):
        incident_acked = IncidentFactory()
        user = PersonUserFactory()
        incident_acked.create_ack(user)
        result = Incident.objects.acked()
        self.assertEqual(result.get(), incident_acked)

    def test_not_acked(self):
        incident_acked = IncidentFactory()
        user = PersonUserFactory()
        # Create an expired ack
        incident_acked.create_ack(user, expiration=self.timestamp)
        result = Incident.objects.not_acked()
        self.assertEqual(set(result), set(Incident.objects.all()))

    def test_has_ticket(self):
        result = Incident.objects.has_ticket()
        self.assertEqual(result.get(), self.incident4)

    def test_lacks_ticket(self):
        result = Incident.objects.lacks_ticket()
        self.assertEqual(set(result), set((self.incident1, self.incident2, self.incident3)))
