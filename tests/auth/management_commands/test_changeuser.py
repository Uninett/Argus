from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase, tag

from argus.auth.factories import PersonUserFactory, AdminUserFactory


User = get_user_model()


def call(command, *args, **options):
    out = StringIO()
    err = StringIO()
    call_command(
        command,
        *args,
        stdout=out,
        stderr=err,
        **options,
    )
    return out.getvalue(), err.getvalue()


@tag("command")
class ChangeUserTests(TestCase):
    def setUp(self):
        self.ordinary_username = "beeblebrox"
        self.ordinary_user = PersonUserFactory(username=self.ordinary_username, is_active=False)
        self.admin_username = "admin"
        self.admin_user = AdminUserFactory(username=self.admin_username)

    def tearDown(self):
        self.ordinary_user.delete()
        self.admin_user.delete()

    @staticmethod
    def call_changeuser(*args, **options):
        return call("changeuser", *args, **options)

    def test_no_args_should_fail(self):
        with self.assertRaises(CommandError):
            self.call_changeuser()

    def test_known_username_should_succeed(self):
        result, error = self.call_changeuser(self.ordinary_username)
        self.assertFalse(error)
        self.assertIn(self.ordinary_username, result)
        user = User.objects.get(username=self.ordinary_username)
        self.assertEqual(self.ordinary_user, user)

    def test_unknown_username_should_fail(self):
        username = "trillian"
        with self.assertRaises(CommandError):
            self.call_changeuser(username)

    def test_setting_stringfields_should_set_stringfields(self):
        # ordinary_user = copy(self.ordinary_user)
        fields = {
            "email": "foo@bar.ca",
            "first_name": "Zaphod",
            "last_name": "Beeblebrox",
        }
        _, error = self.call_changeuser(self.ordinary_username, **fields)
        user = User.objects.get(username=self.ordinary_username)
        self.assertFalse(error)
        for key, value in fields.items():
            with self.subTest("Should not be empty string", key=key):
                result = getattr(user, key, "MISSING")
                self.assertEqual(result, value)

    def test_activate_should_set_is_active_to_True(self):
        orig_is_active = self.ordinary_user.is_active
        self.assertFalse(orig_is_active)
        # activate == active = True
        _, error = self.call_changeuser(self.ordinary_username, active=True)
        self.assertFalse(error)
        user = User.objects.get(username=self.ordinary_username)
        self.assertNotEqual(orig_is_active, user.is_active)
        self.assertTrue(user.is_active)

    def test_deactivate_should_set_is_active_to_False_and_scramble_password(self):
        orig_is_active = self.admin_user.is_active
        self.assertTrue(orig_is_active)
        orig_password = self.admin_user.password
        # deactivate == active = False
        _, error = self.call_changeuser(self.admin_username, active=False)
        self.assertFalse(error)
        user = User.objects.get(username=self.admin_username)
        self.assertNotEqual(orig_is_active, user.is_active)
        self.assertFalse(user.is_active)
        self.assertNotEqual(orig_password, user.password)

    def test_staff_should_set_is_staff_to_True(self):
        orig_is_staff = self.ordinary_user.is_staff
        self.assertFalse(orig_is_staff)
        _, error = self.call_changeuser(self.ordinary_username, staff=True)
        self.assertFalse(error)
        user = User.objects.get(username=self.ordinary_username)
        self.assertNotEqual(orig_is_staff, user.is_staff)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser, "Superuser should be untouched")

    def test_nostaff_should_set_is_staff_to_False(self):
        orig_is_staff = self.admin_user.is_staff
        self.assertTrue(orig_is_staff)
        _, error = self.call_changeuser(self.admin_username, staff=False)
        self.assertFalse(error)
        user = User.objects.get(username=self.admin_username)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_superuser_should_set_is_superuser_and_is_staff_to_True(self):
        orig_is_superuser = self.ordinary_user.is_superuser
        self.assertFalse(orig_is_superuser)
        _, error = self.call_changeuser(self.ordinary_username, superuser=True)
        self.assertFalse(error)
        user = User.objects.get(username=self.ordinary_username)
        self.assertNotEqual(orig_is_superuser, user.is_superuser)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.is_superuser, user.is_staff)

    def test_nosuperuser_should_set_is_superuser_and_is_staff_to_False(self):
        orig_is_superuser = self.admin_user.is_superuser
        self.assertTrue(orig_is_superuser)
        _, error = self.call_changeuser(self.admin_username, superuser=False)
        self.assertFalse(error)
        user = User.objects.get(username=self.admin_username)
        self.assertNotEqual(orig_is_superuser, user.is_superuser)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.is_superuser, user.is_staff)
