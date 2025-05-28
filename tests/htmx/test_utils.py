from datetime import timedelta
from unittest.mock import Mock, patch

from django import test
from django.utils import timezone
from django.test.client import RequestFactory

from argus.htmx.utils import (
    bulk_ack_queryset,
    bulk_change_ticket_url_queryset,
    bulk_close_queryset,
    bulk_reopen_queryset,
    get_qs_for_incident_ids,
    single_autocreate_ticket_url_queryset,
)
from argus.incident.factories import (
    SourceSystemFactory,
    SourceUserFactory,
    StatefulIncidentFactory,
    StatelessIncidentFactory,
)
from argus.incident.models import Incident
from argus.util.testing import connect_signals, disconnect_signals


class TestGetQSForIncidentIDs(test.TestCase):
    def setUp(self):
        disconnect_signals()
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(user=source_user)

    def tearDown(self):
        connect_signals()

    def test_when_given_ids_that_exist_in_default_queryset_it_should_return_all_matching_incidents(self):
        created_incidents = [StatelessIncidentFactory(source=self.source) for _ in range(5)]
        created_ids = [incident.id for incident in created_incidents]
        queryset, missing_ids = get_qs_for_incident_ids(created_ids)
        assert set(created_incidents) == set(queryset)
        assert len(missing_ids) == 0

    def test_when_given_ids_that_exist_in_specified_queryset_it_should_return_all_matching_incidents(self):
        created_incidents = [StatelessIncidentFactory(source=self.source) for _ in range(5)]
        created_ids = [incident.id for incident in created_incidents]
        queryset, missing_ids = get_qs_for_incident_ids(created_ids, Incident.objects.filter(source=self.source))
        assert set(created_incidents) == set(queryset)
        assert len(missing_ids) == 0

    def test_when_given_ids_that_does_not_exist_in_queryset_it_should_include_them_in_missing_ids(self):
        created_incidents = [StatelessIncidentFactory(source=self.source) for _ in range(5)]
        created_ids = [incident.id for incident in created_incidents]
        queryset, missing_ids = get_qs_for_incident_ids(created_ids, Incident.objects.none())
        assert len(queryset) == 0
        assert set(created_ids) == missing_ids


class TestBulkAckQueryset(test.TestCase):
    def setUp(self):
        disconnect_signals()
        request = RequestFactory().get("/foo")
        request.user = SourceUserFactory()
        self.source = SourceSystemFactory(user=request.user)
        self.request = request

    def tearDown(self):
        connect_signals()

    def test_incidents_in_queryset_should_be_acked(self):
        created_incidents = [StatefulIncidentFactory(source=self.source) for _ in range(5)]
        now = timezone.now()
        expiration = now + timedelta(hours=1)
        queryset = Incident.objects.filter(source=self.source)
        assert set(queryset.not_acked()) == set(created_incidents)
        data = {"timestamp": now, "description": "test description", "expiration": expiration}
        bulk_ack_queryset(self.request, queryset, data)
        assert set(queryset.acked()) == set(created_incidents)

    def test_should_return_acked_incidents(self):
        created_incidents = [StatefulIncidentFactory(source=self.source) for _ in range(5)]
        now = timezone.now()
        expiration = now + timedelta(hours=1)
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": now, "description": "test description", "expiration": expiration}
        acked_incidents = bulk_ack_queryset(self.request, queryset, data)
        assert set(acked_incidents) == set(created_incidents)


class TestBulkCloseQueryset(test.TestCase):
    def setUp(self):
        disconnect_signals()
        request = RequestFactory().get("/foo")
        request.user = SourceUserFactory()
        self.source = SourceSystemFactory(user=request.user)
        self.request = request

    def tearDown(self):
        connect_signals()

    def test_incidents_in_queryset_should_be_closed(self):
        created_incidents = [StatefulIncidentFactory(source=self.source) for _ in range(5)]
        now = timezone.now()
        queryset = Incident.objects.filter(source=self.source)
        assert set(queryset.open()) == set(created_incidents)
        data = {"timestamp": now, "description": "test description"}
        bulk_close_queryset(self.request, queryset, data)
        assert set(queryset.closed()) == set(created_incidents)

    def test_should_return_closed_incidents(self):
        created_incidents = [StatefulIncidentFactory(source=self.source) for _ in range(5)]
        now = timezone.now()
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": now, "description": "test description"}
        closed_incidents = bulk_close_queryset(self.request, queryset, data)
        assert set(closed_incidents) == set(created_incidents)


class TestBulkReopenQueryset(test.TestCase):
    def setUp(self):
        disconnect_signals()
        request = RequestFactory().get("/foo")
        request.user = SourceUserFactory()
        self.source = SourceSystemFactory(user=request.user)
        self.request = request

    def tearDown(self):
        connect_signals()

    def test_incidents_in_queryset_should_be_reopened(self):
        now = timezone.now()
        created_incidents = [StatefulIncidentFactory(source=self.source, end_time=now) for _ in range(5)]
        queryset = Incident.objects.filter(source=self.source)
        assert set(queryset.closed()) == set(created_incidents)
        data = {"timestamp": now, "description": "test description"}
        bulk_reopen_queryset(self.request, queryset, data)
        assert set(queryset.open()) == set(created_incidents)

    def test_should_return_reopened_incidents(self):
        now = timezone.now()
        created_incidents = [StatefulIncidentFactory(source=self.source, end_time=now) for _ in range(5)]
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": now, "description": "test description"}
        reopened_incidents = bulk_reopen_queryset(self.request, queryset, data)
        assert set(reopened_incidents) == set(created_incidents)


class TestBulkChangeTicketUrlQueryset(test.TestCase):
    def setUp(self):
        disconnect_signals()
        request = RequestFactory().get("/foo")
        request.user = SourceUserFactory()
        self.source = SourceSystemFactory(user=request.user)
        self.request = request

    def tearDown(self):
        connect_signals()

    def test_ticket_url_for_incidents_in_queryset_should_be_changed_to_new_url(self):
        now = timezone.now()
        initial_ticket_url = "test-url.com"
        new_ticket_url = "new-test-url.com"
        [StatefulIncidentFactory(source=self.source, ticket_url=initial_ticket_url) for _ in range(5)]
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": now, "ticket_url": new_ticket_url}
        bulk_change_ticket_url_queryset(self.request, queryset, data)
        for incident in queryset:
            assert incident.ticket_url == new_ticket_url

    def test_should_return_incidents_in_queryset(self):
        now = timezone.now()
        initial_ticket_url = "test-url.com"
        new_ticket_url = "new-test-url.com"
        created_incidents = [
            StatefulIncidentFactory(source=self.source, ticket_url=initial_ticket_url) for _ in range(5)
        ]
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": now, "ticket_url": new_ticket_url}
        returned_incidents = bulk_change_ticket_url_queryset(self.request, queryset, data)
        assert set(returned_incidents) == set(created_incidents)


class TestSingleAutocreateTicketUrlQueryset(test.TestCase):
    def setUp(self):
        disconnect_signals()
        request = RequestFactory().get("/foo")
        request.user = SourceUserFactory()
        self.source = SourceSystemFactory(user=request.user)
        self.request = request

    def tearDown(self):
        connect_signals()

    def test_should_set_url_for_created_ticket(self):
        initial_url = "test-url-com"
        StatefulIncidentFactory(source=self.source, ticket_url=initial_url)
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": timezone.now()}
        mock_plugin = Mock()
        mocked_url = "mocked-url.com"
        mock_plugin.create_ticket.return_value = mocked_url
        with patch("argus.incident.ticket.utils.get_autocreate_ticket_plugin", return_value=mock_plugin):
            incident = single_autocreate_ticket_url_queryset(self.request, queryset, data)
            assert incident.ticket_url == initial_url

    def test_should_not_update_url_if_incident_already_has_a_ticket_url(self):
        StatefulIncidentFactory(source=self.source, ticket_url="")
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": timezone.now()}
        mock_plugin = Mock()
        mocked_url = "mocked-url.com"
        mock_plugin.create_ticket.return_value = mocked_url
        with patch("argus.incident.ticket.utils.get_autocreate_ticket_plugin", return_value=mock_plugin):
            incident = single_autocreate_ticket_url_queryset(self.request, queryset, data)
            assert incident.ticket_url == mocked_url

    def test_should_raise_exception_if_queryset_contains_more_than_one_result(self):
        [StatefulIncidentFactory(source=self.source) for _ in range(5)]
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": timezone.now()}
        with self.assertRaises(Incident.MultipleObjectsReturned):
            single_autocreate_ticket_url_queryset(self.request, queryset, data)

    def test_should_raise_exception_if_queryset_contains_no_results(self):
        queryset = Incident.objects.filter(source=self.source)
        data = {"timestamp": timezone.now()}
        with self.assertRaises(Incident.DoesNotExist):
            single_autocreate_ticket_url_queryset(self.request, queryset, data)
