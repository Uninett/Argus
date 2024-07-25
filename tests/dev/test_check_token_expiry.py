from datetime import datetime, timedelta
from io import StringIO
import pytz

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from rest_framework.authtoken.models import Token

from argus.dev.management.commands.check_token_expiry import (
    close_expiry_incidents_without_expiring_tokens,
    find_expiring_tokens,
    get_tokens_without_expiry_incident,
)
from argus.auth.factories import SourceUserFactory
from argus.incident.factories import SourceSystemFactory
from argus.incident.models import Incident, IncidentTagRelation, Tag, create_token_expiry_incident
from argus.util.testing import connect_signals, disconnect_signals


class CheckTokenExpiryTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.user1 = SourceUserFactory()
        self.user2 = SourceUserFactory()
        self.source_system1 = SourceSystemFactory(user=self.user1)
        self.source_system2 = SourceSystemFactory(user=self.user2)
        self.expiring_token = Token.objects.create(user=self.user1)
        self.expiring_token.created = self.expiring_token.created - timedelta(days=100)
        self.expiring_token.save()
        self.expiring_token_expiration_date = self.expiring_token.created + timedelta(
            days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS
        )
        self.expiry_incident = create_token_expiry_incident(self.expiring_token, self.expiring_token_expiration_date)

        self.current_token = Token.objects.create(user=self.user2)
        self.current_token_expiration_date = self.current_token.created + timedelta(
            days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS
        )

    def tearDown(self):
        connect_signals()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "check_token_expiry",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

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
        self.assertTrue(create_token_expiry_incident(self.current_token, self.current_token_expiration_date))

    def test_create_token_expiry_incident_raises_error_if_no_given_token(self):
        with self.assertRaises(ValueError):
            create_token_expiry_incident(None, None)

    def test_get_tokens_without_expiry_incident_returns_no_tokens_if_all_have_expiry_incident(self):
        self.assertEqual(
            get_tokens_without_expiry_incident([(self.expiring_token, self.expiring_token_expiration_date)]), []
        )

    def test_get_tokens_without_expiry_incident_returns_token_with_closed_expiry_incident(self):
        current_token_expiry_incident = create_token_expiry_incident(
            self.current_token, self.current_token_expiration_date
        )
        current_token_expiry_incident.set_closed(actor=self.user1)
        self.assertEqual(
            get_tokens_without_expiry_incident([(self.current_token, self.current_token_expiration_date)]),
            [(self.current_token, self.current_token_expiration_date)],
        )

    def test_get_tokens_without_expiry_incident_returns_all_tokens_if_no_open_expiry_incident(self):
        self.expiry_incident.set_closed(actor=self.user1)
        self.assertEqual(
            get_tokens_without_expiry_incident(
                [
                    (self.expiring_token, self.expiring_token_expiration_date),
                    (self.current_token, self.current_token_expiration_date),
                ]
            ),
            [
                (self.expiring_token, self.expiring_token_expiration_date),
                (self.current_token, self.current_token_expiration_date),
            ],
        )

    def test_get_tokens_without_expiry_incident_ignores_other_tokens_expiry_incidents(self):
        self.assertTrue(get_tokens_without_expiry_incident([(self.current_token, self.current_token_expiration_date)]))

    def test_close_expiry_incidents_without_expiring_tokens_does_not_close_connected_incidents(self):
        close_expiry_incidents_without_expiring_tokens([(self.expiring_token, self.expiring_token_expiration_date)])

        self.assertTrue(Incident.objects.get(pk=self.expiry_incident.pk).open)

    def test_close_expiry_incidents_without_expiring_tokens_closes_unconnected_incidents(self):
        close_expiry_incidents_without_expiring_tokens([])
        self.assertFalse(Incident.objects.get(pk=self.expiry_incident.pk).open)

    def test_expiry_incident_is_closed_when_token_deleted(self):
        self.expiring_token.delete()
        self.assertFalse(Incident.objects.get(pk=self.expiry_incident.pk).open)

    def test_expiry_incident_is_closed_when_token_updated(self):
        self.expiring_token.created = datetime.now(pytz.utc)
        self.expiring_token.save()
        self.assertFalse(Incident.objects.get(pk=self.expiry_incident.pk).open)

    def test_check_token_expiry_can_handle_days_input(self):
        days = settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS + 1
        out = self.call_command(f"--days={days}")

        self.assertFalse(out)
        token_expiry_tag = Tag.objects.get(key="problem_type", value="token_expiry")
        source_system_id_tag = Tag.objects.get(key="source_system_id", value=self.current_token.user.source_system.id)

        self.assertTrue(token_expiry_tag)
        self.assertTrue(source_system_id_tag)
        self.assertTrue(
            Incident.objects.filter(incident_tag_relations__tag=token_expiry_tag)
            .filter(incident_tag_relations__tag=source_system_id_tag)
            .exists()
        )
