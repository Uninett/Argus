from django.test import TestCase, tag
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.util.testing import disconnect_signals, connect_signals
from argus.incident.factories import (
    SourceSystemFactory,
    SourceUserFactory,
    StatefulIncidentFactory,
    StatelessIncidentFactory,
)
from argus.incident.models import Incident, Event


class IncidentQuerySetTestCase(TestCase):
    def setUp(self):
        disconnect_signals()
        # Lock in timestamps
        self.timestamp = timezone.now()
        # We don't care about source but let's ensure it is unique
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(user=source_user)
        self.incident1 = StatelessIncidentFactory(source=self.source, start_time=self.timestamp, ticket_url="")
        self.incident2 = StatefulIncidentFactory(source=self.source, start_time=self.timestamp, ticket_url="")
        self.incident3 = StatefulIncidentFactory(source=self.source, start_time=self.timestamp, ticket_url="")
        self.incident4 = StatefulIncidentFactory(source=self.source, start_time=self.timestamp)
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
        incident_acked = StatefulIncidentFactory(source=self.source)
        user = PersonUserFactory()
        incident_acked.create_ack(user)
        result = Incident.objects.acked()
        self.assertEqual(result.get(), incident_acked)

    def test_not_acked(self):
        incident_acked = StatefulIncidentFactory(source=self.source)
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


class IncidentQuerySetUpdatingTestCase(TestCase):
    def setUp(self):
        disconnect_signals()
        # Lock in timestamps
        self.timestamp = timezone.now()
        # We don't care about source but let's ensure it is unique
        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        self.incident1 = StatelessIncidentFactory(source=source, start_time=self.timestamp, ticket_url="")
        self.incident2 = StatefulIncidentFactory(source=source, start_time=self.timestamp, ticket_url="")
        self.incident3 = StatefulIncidentFactory(source=source, start_time=self.timestamp, ticket_url="")
        self.incident4 = StatefulIncidentFactory(source=source, start_time=self.timestamp, end_time=self.timestamp)
        self.source = source
        self.user = PersonUserFactory()

    def tearDown(self):
        connect_signals()

    @tag("bulk")
    def test_create_acks(self):
        qs = Incident.objects.filter(id__in=(self.incident3.id, self.incident4.id))
        qs.create_acks(self.user)
        result = set(Incident.objects.acked())
        self.assertEqual(result, set(qs.all()))

    @tag("bulk")
    def test_create_events(self):
        qs = Incident.objects.filter(id__in=(self.incident3.id, self.incident4.id))
        qs.create_events(self.user, Event.Type.OTHER, description="foo")
        result = set(e.incident for e in Event.objects.filter(type=Event.Type.OTHER))
        self.assertEqual(result, set(qs.all()))

    @tag("bulk")
    def test_update_ticket_url(self):
        qs = Incident.objects.filter(id__in=(self.incident1.id, self.incident2.id))
        qs.update_ticket_url(self.user, "http://vg.no")
        result = qs.has_ticket()
        self.assertEqual(set(result), set(qs.all()))

    @tag("bulk")
    def test_close_incidents(self):
        qs = Incident.objects.filter(id__in=(self.incident2.id, self.incident3.id))
        qs.close(self.user, description="Boo")
        result = set(e.incident for e in Event.objects.filter(type=Event.Type.CLOSE, description="Boo"))
        self.assertEqual(result, set(qs.all()))

    @tag("bulk")
    def test_reopen_incidents(self):
        self.incident2.set_closed(self.user)
        self.incident3.set_closed(self.user)
        qs = Incident.objects.filter(id__in=(self.incident2.id, self.incident3.id))
        qs.reopen(self.user, description="Bar")
        result = set(e.incident for e in Event.objects.filter(type=Event.Type.REOPEN, description="Bar"))
        self.assertEqual(result, set(qs.all()))
