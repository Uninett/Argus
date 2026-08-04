from django import forms
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import DestinationConfigFactory
from argus.notificationprofile.media.base import NotificationMedium
from argus.notificationprofile.models import Media


class DummyNotification(NotificationMedium):
    MEDIA_SETTINGS_KEY = "foo"
    MEDIA_NAME = "Dummy"
    MEDIA_SLUG = "dummy"

    class Form(forms.Form):
        foo = forms.IntegerField()


class ValidateSettingsTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()

    def test_given_valid_settings_then_return_cleaned_data(self):
        data = {"foo": 1}
        cleaned_data = DummyNotification().validate_settings(data, self.user)

        self.assertEqual(cleaned_data, data)

    def test_given_settings_with_missing_key_then_raise_validation_error(self):
        data = {"bar": False}
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate_settings(data, self.user)

        self.assertIn("required", str(e.exception))

    def test_given_settings_with_wrong_type_then_raise_validation_error(self):
        data = {"foo": False}
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate_settings(data, self.user)

        self.assertIn("whole number", str(e.exception))

    def test_given_duplicate_settings_then_raise_validation_error(self):
        settings = {"foo": 1}
        dummy_medium = Media.objects.create(slug=DummyNotification().MEDIA_SLUG, name=DummyNotification().MEDIA_NAME)
        DestinationConfigFactory(
            user=self.user,
            media=dummy_medium,
            settings=settings,
            managed=False,
        )

        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate_settings(settings, self.user)

        self.assertIn(DummyNotification().error_messages["duplicate"], str(e.exception))

    def test_given_duplicate_settings_for_same_destination_then_do_not_raise_validation_error(self):
        settings = {"foo": 1}
        dummy_medium = Media.objects.create(slug=DummyNotification().MEDIA_SLUG, name=DummyNotification().MEDIA_NAME)
        destination = DestinationConfigFactory(
            user=self.user,
            media=dummy_medium,
            settings=settings,
            managed=False,
        )

        cleaned_data = DummyNotification().validate_settings(settings, self.user, destination)

        self.assertEqual(cleaned_data, settings)


class ValidateTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.dummy_medium = Media.objects.create(slug=DummyNotification.MEDIA_SLUG, name=DummyNotification.MEDIA_NAME)
        self.destination = DestinationConfigFactory(
            user=self.user,
            media=self.dummy_medium,
            settings={"foo": 999},
            managed=False,
        )

    def test_given_valid_data_for_new_destination_then_return_form(self):
        data = {
            "media": self.dummy_medium,
            "label": "Dummy destination",
            "settings": {"foo": 1},
        }
        form = DummyNotification().validate(data, self.user)

        self.assertEqual(form.cleaned_data["label"], data["label"])
        self.assertEqual(form.cleaned_data["settings"], data["settings"])

    def test_given_valid_data_for_existing_destination_then_return_form(self):
        data = {
            "media": self.dummy_medium,
            "label": "Dummy destination",
            "settings": {"foo": 1},
        }
        form = DummyNotification().validate(data, self.user, self.destination)

        self.assertEqual(form.cleaned_data["label"], data["label"])
        self.assertEqual(form.cleaned_data["settings"], data["settings"])

    def test_given_changed_media_then_raise_validation_error(self):
        different_medium = Media.objects.create(slug="different", name="Different medium")
        data = {
            "media": different_medium,
            "settings": {"foo": 1},
        }
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate(data, self.user, self.destination)

        self.assertIn(DummyNotification.error_messages["readonly_media"], str(e.exception))

    def test_given_changed_user_then_raise_validation_error(self):
        other_user = PersonUserFactory()
        data = {
            "media": self.dummy_medium,
            "settings": {"foo": 1},
        }
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate(data, other_user, self.destination)

        self.assertIn(DummyNotification.error_messages["readonly_user"], str(e.exception))

    def test_given_invalid_medium_for_new_destination_then_raise_validation_error(self):
        data = {
            "media": "invalid",
            "settings": {"foo": 1},
        }
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate(data, self.user)

        self.assertIn("Select a valid choice.", str(e.exception))

    def test_given_duplicate_label_then_raise_validation_error(self):
        self.destination.label = "Duplicate label"
        self.destination.save()
        data = {
            "media": self.dummy_medium,
            "label": "Duplicate label",
            "settings": {"foo": 1},
        }
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate(data, self.user)

        self.assertIn(DummyNotification.error_messages["duplicate_label"], str(e.exception))

    def test_given_same_label_for_given_destination_then_do_not_raise_validation_error(self):
        self.destination.label = "Duplicate label"
        self.destination.save()
        data = {
            "media": self.dummy_medium,
            "label": "Duplicate label",
            "settings": {"foo": 1},
        }
        form = DummyNotification().validate(data, self.user, self.destination)

        self.assertEqual(form.cleaned_data["label"], "Duplicate label")

    def test_given_non_dict_settings_then_raise_validation_error(self):
        data = {
            "media": self.dummy_medium,
            "settings": 100,
        }
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate(data, self.user)

        self.assertIn(DummyNotification.error_messages["settings_type"], str(e.exception))

    def test_given_empty_settings_then_raise_validation_error(self):
        data = {
            "media": self.dummy_medium,
            "settings": {},
        }
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate(data, self.user)

        self.assertIn(DummyNotification.error_messages["empty_settings"], str(e.exception))

    def test_given_invalid_settings_then_raise_validation_error(self):
        data = {
            "media": self.dummy_medium,
            "settings": {"bar": "wrong"},
        }
        with self.assertRaises(ValidationError) as e:
            DummyNotification().validate(data, self.user)

        self.assertIn("required", str(e.exception))
