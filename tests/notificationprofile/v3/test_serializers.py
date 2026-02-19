from django.test import tag, TestCase

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.v3.serializers import DestinationConfigSerializer


@tag("db")
class DestinationConfigSerializerTest(TestCase):
    def test_get_suggested_label_should_be_generated(self):
        user = PersonUserFactory()
        destination = user.destinations.first()
        serializer = DestinationConfigSerializer(destination)
        self.assertEqual(serializer.data["suggested_label"], serializer.get_suggested_label(destination))

    def test_settings_should_not_contain_synced(self):
        user = PersonUserFactory()
        destination = user.destinations.first()
        serializer = DestinationConfigSerializer(destination)
        self.assertNotIn("synced", serializer.data["settings"].keys())
