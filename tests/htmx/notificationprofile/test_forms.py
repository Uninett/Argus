from django.test import tag, TestCase

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.htmx.notificationprofile.views import NotificationProfileForm
from argus.notificationprofile.factories import NotificationProfileFactory, TimeslotFactory
from argus.util.testing import connect_signals, disconnect_signals


@tag("integration")
class NotificationProfileFormTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.user = PersonUserFactory()

        self.name1 = "abc"
        self.name2 = "def"

        self.timeslot = TimeslotFactory(user=self.user, name="Never")

        self.notification_profile1 = NotificationProfileFactory(name=self.name1, user=self.user, timeslot=self.timeslot)
        self.notification_profile2 = NotificationProfileFactory(name=self.name2, user=self.user, timeslot=self.timeslot)

        self.filter = FilterFactory(user=self.user)

    def teardown(self):
        connect_signals()

    def test_form_with_different_name_as_other_profiles_is_valid(self):
        data = {
            "name": "different name",
            "timeslot": self.notification_profile1.timeslot,
            "filters": [self.filter],
        }
        form = NotificationProfileForm(data=data, user=self.notification_profile1.user)

        self.assertTrue(form.is_valid())

    def test_form_with_same_name_as_other_profile_is_invalid(self):
        data = {
            "name": self.name1,
            "timeslot": self.notification_profile1.timeslot,
            "filters": [self.filter],
        }
        form = NotificationProfileForm(data=data, user=self.notification_profile1.user)
        self.assertFalse(form.is_valid())
        self.assertFormError(
            form=form, field="name", errors=f"A profile by this user with the name '{self.name1}' already exists."
        )

    def test_updating_form_with_same_name_as_self_is_valid(self):
        data = {
            "name": self.name1,
            "timeslot": self.notification_profile1.timeslot,
            "filters": [self.filter],
        }
        form = NotificationProfileForm(
            data=data, instance=self.notification_profile1, user=self.notification_profile1.user
        )

        self.assertTrue(form.is_valid())

    def test_updating_form_with_same_name_as_other_profile_is_invalid(self):
        data = {
            "name": self.name2,
            "timeslot": self.notification_profile1.timeslot,
            "filters": [self.filter],
        }
        form = NotificationProfileForm(
            data=data, instance=self.notification_profile1, user=self.notification_profile1.user
        )
        self.assertFalse(form.is_valid())
        self.assertFormError(
            form=form, field="name", errors=f"A profile by this user with the name '{self.name2}' already exists."
        )
