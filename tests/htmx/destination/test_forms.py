from django.test import TestCase

from argus.htmx.destination.forms import DestinationFormUpdate
from argus.notificationprofile.factories import DestinationConfigFactory, MediaFactory


class TestDestinationFormUpdate(TestCase):
    def test_given_uninstalled_medium_it_should_disable_editing(self):
        uninstalled_media = MediaFactory(installed=False)
        destination = DestinationConfigFactory(media=uninstalled_media, settings={"test_key": "test_val"})

        form = DestinationFormUpdate(instance=destination)

        self.assertTrue(form.fields["label"].disabled)
        self.assertTrue(form.fields["settings"].disabled)
