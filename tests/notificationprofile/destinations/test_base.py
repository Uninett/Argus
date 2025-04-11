from unittest import skip

from django import forms
from django.test import TestCase, tag
from rest_framework.exceptions import ValidationError

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.media.base import NotificationMedium


class DummyNotification(NotificationMedium):
    MEDIA_SETTINGS_KEY = "foo"
    MEDIA_NAME = "Dummy"
    MEDIA_SLUG = "dummy"

    class Form(forms.Form):
        foo = forms.IntegerField()


@tag("unit")
class NotificationMediumValidateSettingsTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()

    def test_is_not_valid_on_wrong_settings(self):
        data = {"bar": False}
        form = DummyNotification.validate_settings(data, self.user)
        self.assertFalse(form.is_valid())
        errors = form.errors.get_json_data()
        self.assertEqual(errors["foo"][0]["message"], "This field is required.")


@tag("unit")
@skip("unfinished, needs instance of media type")
class NotificationMediumValidateTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()

    def test_croaks_on_non_dict_settings(self):
        data = {"settings": None}
        with self.assertRaises(ValidationError) as e:
            DummyNotification.validate(data, self.user)
        foo_error = e.exception
        self.assertEqual(foo_error.message, DummyNotification.error_messages["settings_type"])

    def test_croaks_on_empty_settings(self):
        data = {"settings": {}}
        with self.assertRaises(ValidationError) as e:
            DummyNotification.validate(data, self.user)
        foo_error = e.exception
        self.assertEqual(foo_error.message, DummyNotification.error_messages["empty_settings"])

    def test_croaks_if_plugin_not_loaded(self):
        data = {
            "media": DummyNotification.MEDIA_SLUG,
            "settings": {"foo": 1},
        }
        with self.assertRaises(ValidationError) as e:
            DummyNotification.validate(data, self.user)
        self.assertIn("media", e.exception.error_dict)
        media_error = e.exception.error_dict["media"][0]
        self.assertEqual(media_error.message, "Select a valid choice. That choice is not one of the available choices.")
