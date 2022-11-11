from datetime import datetime, timedelta
import pytz

from django.conf import settings
from django.test import TestCase
from rest_framework.authtoken.models import Token

from argus.dev.management.commands.check_token_expiry import (
    close_expiry_incidents_without_expiring_tokens,
    find_expiring_tokens,
    get_tokens_without_expiry_incident,
)
from argus.incident.factories import SourceSystemFactory
from argus.incident.models import Incident, create_token_expiry_incident
from argus.util.testing import connect_signals, disconnect_signals


class CheckTokenExpiryTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.source_system1 = SourceSystemFactory()
        self.source_system2 = SourceSystemFactory()
        self.user1 = self.source_system1.user
        self.user2 = self.source_system2.user
        self.expiring_token = Token.objects.create(user=self.user1)
        self.expiring_token.created = self.expiring_token.created - timedelta(days=100)
        self.expiring_token.save()
        self.expiring_token_expiration_date = self.expiring_token.created + timedelta(
            days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS
        )
        self.current_token = Token.objects.create(user=self.user2)
        self.current_token_expiration_date = self.current_token.created + timedelta(
            days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS
        )

    def tearDown(self):
        connect_signals()

    def _create_token_expiry_incident(self):
        return create_token_expiry_incident(
            self.expiring_token,
            self.expiring_token_expiration_date,
        )

    def test_find_token_expiry_finds_only_expiring_token(self):
        self.assertEqual(
            find_expiring_tokens(5),
            [
                (
                    self.expiring_token,
                    self.expiring_token_expiration_date,
                )
            ],
        )

    def test_create_token_expiry_incident_creates_incident(self):
        self.assertTrue(self._create_token_expiry_incident())

    def test_create_token_expiry_incident_raises_error_if_no_given_token(self):
        with self.assertRaises(ValueError):
            create_token_expiry_incident(None, None)

    def test_get_tokens_without_expiry_incident_finds_expiry_incident(self):
        self._create_token_expiry_incident()
        self.assertEqual(
            get_tokens_without_expiry_incident([(self.expiring_token, self.expiring_token_expiration_date)]), []
        )

    def test_get_tokens_without_expiry_incident_ignores_other_tokens_expiry_incidents(self):
        self._create_token_expiry_incident()
        self.assertTrue(get_tokens_without_expiry_incident([(self.current_token, self.expiring_token_expiration_date)]))

    def test_close_expiry_incidents_without_expiring_tokens_does_not_close_connected_incidents(self):
        expiry_incident_pk = self._create_token_expiry_incident().pk
        close_expiry_incidents_without_expiring_tokens([(self.expiring_token, self.expiring_token_expiration_date)])

        self.assertTrue(Incident.objects.open().filter(pk=expiry_incident_pk).exists())

    def test_close_expiry_incidents_without_expiring_tokens_closes_unconnected_incidents(self):
        expiry_incident_pk = self._create_token_expiry_incident().pk
        close_expiry_incidents_without_expiring_tokens([])
        self.assertTrue(Incident.objects.closed().filter(pk=expiry_incident_pk).exists())

    def test_expiry_incident_is_closed_when_token_deleted(self):
        self._create_token_expiry_incident()
        self.expiring_token.delete()
        self.assertFalse(Incident.objects.first().open)

    def test_expiry_incident_is_closed_when_token_updated(self):
        self._create_token_expiry_incident()
        self.expiring_token.created = datetime.now(pytz.utc)
        self.expiring_token.save()
        self.assertFalse(Incident.objects.first().open)
