from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from argus.auth.models import User
from argus.incident.models import SourceSystem, SourceSystemType
from argus.util.testing import connect_signals, disconnect_signals


class CreateFakeIncidentTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        call_command(
            "initial_setup",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    def test_initial_setup_will_create_superuser_and_default_instances(self):
        out, err = self.call_command()

        self.assertFalse(err)

        self.assertTrue(User.objects.filter(username="argus", is_superuser=True).exists())
        self.assertTrue(SourceSystem.objects.filter(name="argus").exists())
        self.assertTrue(SourceSystemType.objects.filter(name="argus").exists())

        self.assertTrue(User.objects.filter(username="admin", is_superuser=True).exists())

    def test_initial_setup_will_create_superuser_with_set_email(self):
        out, err = self.call_command("--username=admin2")

        self.assertFalse(err)

        self.assertTrue(User.objects.filter(username="admin2", is_superuser=True).exists())

    def test_initial_setup_will_create_superuser_with_set_username(self):
        out, err = self.call_command("--email=test@example.com")

        self.assertFalse(err)

        self.assertEqual(User.objects.get(username="admin", is_superuser=True).email, "test@example.com")

    def test_initial_setup_will_create_superuser_with_set_password(self):
        out, err = self.call_command("--password=12344321")

        self.assertFalse(err)

        self.assertEqual(
            out,
            'Ensured the existence of the source, source type and user "argus"\nSuccessfully created Argus superuser "admin" with the chosen password\n',
        )

    def test_initial_setup_will_display_error_message_if_called_twice(self):
        self.call_command()
        out, err = self.call_command()

        self.assertEqual(out, 'Ensured the existence of the source, source type and user "argus"\n')
        self.assertEqual(err, "Argus superuser admin already exists!\n")
