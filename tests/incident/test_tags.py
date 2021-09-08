from datetime import datetime, timedelta

from django.db.models import signals
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.test import APITestCase

from argus.util import datetime_utils
from argus.util.utils import duplicate
from argus.util.testing import disconnect_signals, connect_signals
from argus.incident.factories import StatefulIncidentFactory, SourceSystemFactory
from argus.incident.models import Event, Incident
from . import IncidentBasedAPITestCaseHelper


class IncidentTagViewSetTests(APITestCase, IncidentBasedAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()

        super().init_test_objects()

        self.stateful_incident1 = StatefulIncidentFactory(
            source=self.source1,
            source_incident_id="1",
        )

    def tearDown(self):
        connect_signals()

    def test_view_V1_incident_tags_when_no_tags(self):
        incident = StatefulIncidentFactory()
        self.assertFalse(incident.deprecated_tags)
        response = self.user1_rest_client.get(reverse("v1:incident:incident-tags", kwargs={"incident_pk": incident.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_view_incident_tags_when_some_tags(self):
        incident = StatefulIncidentFactory()
