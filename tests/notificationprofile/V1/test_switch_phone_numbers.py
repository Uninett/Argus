from django.test import TestCase

from phonenumber_field.phonenumber import PhoneNumber

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import DestinationConfigFactory, NotificationProfileFactory
from argus.notificationprofile.media import MEDIA_CLASSES_DICT
from argus.notificationprofile.V1.serializers import _switch_phone_numbers


class SwitchPhoneNumberTests(TestCase):
    def setUp(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            return

        self.user = PersonUserFactory()
        self.profile = NotificationProfileFactory(user=self.user)
        self.destination = DestinationConfigFactory(
            user=self.user,
            media_id="sms",
            settings={"phone_number": "+4747474746"},
        )
        self.profile.destinations.add(self.destination)
        self.new_phone_number = PhoneNumber.from_string("+4747474747")

    def test_switch_phone_number(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            self.skipTest("No sms plugin available")

        _switch_phone_numbers(self.destination, self.new_phone_number, self.profile)

        self.assertEqual(
            self.profile.destinations.order_by("pk").first().settings["phone_number"], self.new_phone_number.as_e164
        )
