from datetime import timedelta
from unittest.mock import patch

from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404, QueryDict
from django.test import RequestFactory, TestCase, override_settings
from django.utils.timezone import now as django_now

from argus.auth.factories import (
    PersonUserFactory,
)
from argus.filter.factories import FilterFactory
from argus.htmx.incident.views import filter_select, incident_detail, incident_update
from argus.incident.factories import (
    IncidentFactory,
    StatefulIncidentFactory,
)
from argus.incident.models import Incident
from argus.notificationprofile.models import Filter
from argus.util.testing import connect_signals, disconnect_signals


@override_settings(
    ROOT_URLCONF="argus.htmx.root_urls",
)
class TestIncidentDetail(TestCase):
    def setUp(self) -> None:
        disconnect_signals()
        self.factory = RequestFactory()
        self.request = self.factory.get("mockurl")
        self.request.user = PersonUserFactory()
        SessionMiddleware(lambda x: x).process_request(self.request)
        MessageMiddleware(lambda x: x).process_request(self.request)
        self.incident = IncidentFactory()

    def teardown(self):
        connect_signals()

    def test_should_404_if_unknown_pk(self):
        # newest incident should have the highest pk, so pk+1 should not exist
        invalid_pk = self.incident.pk + 1
        assert not Incident.objects.filter(pk=invalid_pk).exists()
        with self.assertRaises(Http404):
            incident_detail(self.request, invalid_pk)

    def test_should_200_if_existing_pk(self):
        response = incident_detail(self.request, self.incident.pk)
        self.assertEqual(response.status_code, 200)

    def test_should_render_page_for_correct_incident(self):
        response = incident_detail(self.request, self.incident.pk)
        # Only the correct details page should have the string representation of the object
        self.assertContains(response, str(self.incident))

    def test_should_calculate_correct_duration_for_active_incident(self):
        now = django_now()
        start_time = now - timedelta(hours=2)
        incident = StatefulIncidentFactory(start_time=start_time)
        duration = now - start_time
        with patch("argus.htmx.incident.views.tznow", return_value=now):
            response = incident_detail(self.request, incident.pk)
            self.assertContains(response, str(duration))

    def test_should_calculate_correct_duration_for_ended_incident(self):
        now = django_now()
        start_time = now - timedelta(hours=2)
        end_time = now - timedelta(hours=1)
        incident = StatefulIncidentFactory(start_time=start_time, end_time=end_time)
        duration = end_time - start_time
        with patch("argus.htmx.incident.views.tznow", return_value=now):
            response = incident_detail(self.request, incident.pk)
            self.assertContains(response, str(duration))


class TestIncidentUpdate(TestCase):
    def setUp(self) -> None:
        disconnect_signals()
        self.factory = RequestFactory()
        self.request = self.factory.post("mockurl")
        self.request.user = PersonUserFactory()
        SessionMiddleware(lambda x: x).process_request(self.request)
        MessageMiddleware(lambda x: x).process_request(self.request)
        self.incident = IncidentFactory()

    def teardown(self):
        connect_signals()

    def test_ack_action_should_ack_incidents(self):
        self.request.POST = QueryDict(f"incident_ids={self.incident.pk}")
        assert not self.incident.acked
        incident_update(self.request, "ack")
        assert self.incident.acked

    def test_created_ack_event_should_have_correct_description(self):
        description = "testdescr"
        self.request.POST = QueryDict(f"incident_ids={self.incident.pk}&description={description}")
        incident_update(self.request, "ack")
        ack = self.incident.acks.first()
        self.assertEqual(ack.event.description, description)


class TestFilterSelect(TestCase):
    def setUp(self) -> None:
        disconnect_signals()
        self.factory = RequestFactory()
        self.request = self.factory.get("mockurl")
        self.request.user = PersonUserFactory()
        SessionMiddleware(lambda x: x).process_request(self.request)
        MessageMiddleware(lambda x: x).process_request(self.request)
        self.incident = IncidentFactory()
        self.filter = FilterFactory()

    def teardown(self):
        connect_signals()

    def test_should_200_if_existing_pk(self):
        self.request.GET = QueryDict(f"filter={self.filter.pk}")
        response = filter_select(self.request)
        self.assertEqual(response.status_code, 200)

    def test_should_404_if_unknown_pk(self):
        # newest incident should have the highest pk, so pk+1 should not exist
        invalid_pk = self.filter.pk + 1
        self.request.GET = QueryDict(f"filter={invalid_pk}")
        assert not Filter.objects.filter(pk=invalid_pk).exists()
        with self.assertRaises(Http404):
            filter_select(self.request)

    def test_should_update_session_with_selected_filter(self):
        self.request.GET = QueryDict(f"filter={self.filter.pk}")
        filter_select(self.request)
        self.assertEqual(int(self.request.session["selected_filter"]), self.filter.pk)
