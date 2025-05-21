from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase, tag

from argus.auth.factories import PersonUserFactory


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
class CreateUserTests(TestCase):
    @staticmethod
    def call_createuser(*args, **options):
        return call("createuser", *args, **options)

    def test_no_args_should_fail(self):
        with self.assertRaises(CommandError):
            self.call_createuser()

    def test_unknown_username_should_succeed(self):
        username = "beeblebrox"
        result, error = self.call_createuser(username)
        self.assertFalse(error)
        self.assertIn(username, result)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.fail("User not created")
        # field defaults
        boolean_fields = ("is_active", "is_staff", "is_superuser")
        for field in boolean_fields:
            with self.subTest("Should be False", field=field):
                self.assertFalse(getattr(user, field, True))
        string_fields = ("email", "first_name", "last_name")
        for field in string_fields:
            with self.subTest("Should be empty string", field=field):
                self.assertEqual(getattr(user, field, "BLBL"), "")

    def test_known_username_should_fail(self):
        username = "beeblebrox"
        PersonUserFactory(username=username)
        with self.assertRaises(CommandError):
            self.call_createuser(username)

    def test_setting_stringfields_should_set_stringfields(self):
        username = "beeblebrox"
        fields = {
            "email": "foo@bar.ca",
            "first_name": "Zaphod",
            "last_name": "Beeblebrox",
        }
        _, error = self.call_createuser(username, **fields)
        user = User.objects.get(username=username)
        self.assertFalse(error)
        for key, value in fields.items():
            with self.subTest("Should not be empty string", key=key):
                result = getattr(user, key, "MISSING")
                self.assertEqual(result, value)

    def test_is_active_should_set_is_active_to_True(self):
        username = "beeblebrox"
        result, error = self.call_createuser(username, is_active=True)
        self.assertFalse(error)
        user = User.objects.get(username=username)
        self.assertTrue(user.is_active)

    def test_is_staff_should_set_is_staff_to_True(self):
        username = "beeblebrox"
        result, error = self.call_createuser(username, is_staff=True)
        self.assertFalse(error)
        user = User.objects.get(username=username)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_is_superuser_should_set_is_superuser_and_is_staff_to_True(self):
        username = "beeblebrox"
        result, error = self.call_createuser(username, is_superuser=True)
        self.assertFalse(error)
        user = User.objects.get(username=username)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
