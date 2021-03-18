from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.utils.timezone import is_aware, make_aware

from rest_framework import serializers, versioning

from argus.auth.factories import SourceUserFactory
from argus.incident.factories import *
from argus.incident.models import Event
from argus.incident.views import EventViewSet
from argus.util.testing import disconnect_signals, connect_signals


class EventViewSetTestCase(TestCase):
    def setUp(self):
        disconnect_signals()
        source_type = SourceSystemTypeFactory()
        source_user = SourceUserFactory()
        self.source = SourceSystemFactory(type=source_type, user=source_user)

    def tearDown(self):
        connect_signals()

    def test_validate_event_type_for_incident_acknowledge_raises_validation_error(self):
        incident = IncidentFactory(source=self.source)
        viewfactory = RequestFactory()
        request = viewfactory.get(f"/api/v1/incidents/{incident.pk}/events/")
        request.versioning_scheme = versioning.NamespaceVersioning()
        request.version = "v1"
        view = EventViewSet()
        view.request = request
        with self.assertRaises(serializers.ValidationError):
            view.validate_event_type_for_incident(Event.Type.ACKNOWLEDGE, incident)
