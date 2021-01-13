from django.test import TestCase

from argus.notificationprofile.factories import TimeslotFactory
from argus.notificationprofile.media.email import modelinstance_to_dict


class SerializeModelTest(TestCase):
    def test_modelinstance_to_dict_should_not_change_modelinstance(self):
        instance = TimeslotFactory()
        attributes1 = vars(instance)
        modelinstance_to_dict(instance)
        attributes2 = vars(instance)
        self.assertEqual(attributes1, attributes2)
