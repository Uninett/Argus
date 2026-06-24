from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from argus.notificationprofile.factories import NotificationProfileFactory
from argus.notificationprofile.models import NotificationProfile
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
            "toggle_profile_activation",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    def test_toggle_profile_activation_should_activate_inactivate_profile(self):
        profile = NotificationProfileFactory(active=False)

        out, err = self.call_command(profile.id)

        self.assertFalse(out)
        self.assertFalse(err)
        profile.refresh_from_db()
        self.assertTrue(profile.active)

    def test_toggle_profile_activation_should_deactivate_active_profile(self):
        profile = NotificationProfileFactory(active=True)

        out, err = self.call_command(profile.id)

        self.assertFalse(out)
        self.assertFalse(err)
        profile.refresh_from_db()
        self.assertFalse(profile.active)

    def test_toggle_profile_activation_should_toggle_multiple_profiles(self):
        active_profile = NotificationProfileFactory(active=True)
        inactive_profile = NotificationProfileFactory(active=False)

        out, err = self.call_command(active_profile.id, inactive_profile.id)

        self.assertFalse(out)
        self.assertFalse(err)
        active_profile.refresh_from_db()
        inactive_profile.refresh_from_db()
        self.assertFalse(active_profile.active)
        self.assertTrue(inactive_profile.active)

    def test_toggle_profile_activation_should_raise_error_for_invalid_id(self):
        invalid_profile_id = NotificationProfile.objects.last().id + 1 if NotificationProfile.objects.exists() else 1

        _, err = self.call_command(invalid_profile_id)

        self.assertEqual(err, "No profiles with the given ids could be found.\n")

    def test_toggle_profile_activation_should_report_error_but_update_for_partially_found_ids(self):
        profile = NotificationProfileFactory(active=True)
        invalid_profile_id = NotificationProfile.objects.last().id + 1

        _, err = self.call_command(profile.id, invalid_profile_id)

        self.assertEqual(
            err,
            f"Profiles with the ids {{{invalid_profile_id}}} could not be found. Toggling activation of the remaining found profiles with the ids {{{profile.id}}}.\n",
        )
        profile.refresh_from_db()
        self.assertFalse(profile.active)

    def test_toggle_profile_activation_should_raise_error_for_missing_ids(self):
        with self.assertRaises(CommandError):
            self.call_command()
