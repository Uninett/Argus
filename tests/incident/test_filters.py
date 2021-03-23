from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import is_aware, make_aware

from argus.auth.factories import SourceUserFactory
from argus.util.testing import disconnect_signals, connect_signals
from argus.incident.factories import *
from argus.incident.models import Incident, IncidentTagRelation
from argus.incident.views import IncidentFilter


class IncidentBasedAPITestCaseHelper:
    def init_test_objects(self):
        self.source_type = SourceSystemTypeFactory(name="nav")
        self.source1_user = SourceUserFactory(username="nav1")
        self.source1 = SourceSystemFactory(name="NAV 1", type=self.source_type, user=self.source1_user)
        self.source2_user = SourceUserFactory(username="nav2")
        self.source2 = SourceSystemFactory(name="NAV 2", type=self.source_type, user=self.source2_user)


class IncidentFilterTestCase(IncidentBasedAPITestCaseHelper, TestCase):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()
        self.incident1 = IncidentFactory(source=self.source1, end_time=None, ticket_url="")
        self.incident2 = IncidentFactory(source=self.source1, ticket_url="")
        self.incident3 = IncidentFactory(source=self.source2, ticket_url="")
        self.incident4 = IncidentFactory(source=self.source2)
        self.incident4.end_time = self.incident4.start_time
        self.incident4.save()

    def tearDown(self):
        connect_signals()

    def test_stateful_true(self):
        qs = Incident.objects.order_by("pk")
        expected = qs.stateful()
        result = IncidentFilter.incident_filter(qs, "stateful", True)
        self.assertEqual(list(expected), list(result.order_by("pk")))

    def test_stateful_false(self):
        qs = Incident.objects.order_by("pk")
        expected = qs.stateless()
        result = IncidentFilter.incident_filter(qs, "stateful", False)
        self.assertEqual(list(expected), list(result.order_by("pk")))

    def test_open_true(self):
        qs = Incident.objects.order_by("pk")
        expected = qs.open()
        result = IncidentFilter.incident_filter(qs, "open", True)
        self.assertEqual(list(expected), list(result.order_by("pk")))

    def test_open_false(self):
        qs = Incident.objects.order_by("pk")
        expected = qs.closed()
        result = IncidentFilter.incident_filter(qs, "open", False)
        self.assertEqual(list(expected), list(result.order_by("pk")))

    def test_ticket_true(self):
        qs = Incident.objects.order_by("pk")
        expected = qs.has_ticket()
        result = IncidentFilter.incident_filter(qs, "ticket", True)
        self.assertEqual(list(expected), list(result.order_by("pk")))

    def test_ticket_false(self):
        qs = Incident.objects.order_by("pk")
        expected = qs.lacks_ticket()
        result = IncidentFilter.incident_filter(qs, "ticket", False)
        self.assertEqual(list(expected), list(result.order_by("pk")))

    def test_tags_single(self):
        user = SourceUserFactory()
        tag1 = TagFactory(key="testkey1", value="testvalue1")
        tag2 = TagFactory(key="testkey2", value="testvalue2")
        incident5 = IncidentFactory(source=self.source1)
        for incident in (self.incident1, self.incident2, self.incident3):
            IncidentTagRelation.objects.get_or_create(tag=tag1, incident=incident, added_by=user)
        for incident in (self.incident3, self.incident4, incident5):
            IncidentTagRelation.objects.get_or_create(tag=tag1, incident=incident, added_by=user)

        qs = Incident.objects.order_by("pk")

        expected = qs.from_tags(str(tag1))
        result = IncidentFilter.incident_filter(qs, "tags", str(tag1))
        self.assertEqual(list(expected), list(result.order_by("pk")))

    def test_tags_multiple_same_key(self):
        user = SourceUserFactory()
        tag1 = TagFactory(key="testkey", value="testvalue1")
        tag2 = TagFactory(key="testkey", value="testvalue2")
        incident5 = IncidentFactory(source=self.source1)
        for incident in (self.incident1, self.incident2, self.incident3):
            IncidentTagRelation.objects.get_or_create(tag=tag1, incident=incident, added_by=user)
        for incident in (self.incident3, self.incident4, incident5):
            IncidentTagRelation.objects.get_or_create(tag=tag1, incident=incident, added_by=user)

        qs = Incident.objects.order_by("pk")

        expected = qs.from_tags(str(tag1), str(tag2))
        result = IncidentFilter.incident_filter(qs, "tags", [str(tag1), str(tag2)])
        self.assertEqual(list(expected), list(result.order_by("pk")))

    def test_tags_multiple_different_key(self):
        user = SourceUserFactory()
        tag1 = TagFactory(key="testkey1", value="testvalue1")
        tag2 = TagFactory(key="testkey2", value="testvalue2")
        incident5 = IncidentFactory(source=self.source1)
        for incident in (self.incident1, self.incident2, self.incident3):
            IncidentTagRelation.objects.get_or_create(tag=tag1, incident=incident, added_by=user)
        for incident in (self.incident3, self.incident4, incident5):
            IncidentTagRelation.objects.get_or_create(tag=tag1, incident=incident, added_by=user)

        qs = Incident.objects.order_by("pk")

        expected = qs.from_tags(str(tag1), str(tag2))
        result = IncidentFilter.incident_filter(qs, "tags", [str(tag1), str(tag2)])
        self.assertEqual(list(expected), list(result.order_by("pk")))
