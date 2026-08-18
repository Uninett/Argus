from django.test import TestCase

from argus.htmx.destination.forms import DestinationFormCreate, DestinationFormUpdate
from argus.notificationprofile.factories import DestinationConfigFactory, MediaFactory


class TestDestinationForm(TestCase):
    def test_given_medium_with_no_plugin_it_should_not_be_a_valid_choice(self):
        fake_media = MediaFactory()
        form = DestinationFormCreate()

        self.assertNotIn(fake_media, form.fields["media"].queryset)

    def test_given_uninstalled_medium_it_should_disable_editing(self):
        uninstalled_media = MediaFactory(installed=False)
        destination = DestinationConfigFactory(media=uninstalled_media, settings={"test_key": "test_val"})

        form = DestinationFormUpdate(instance=destination)

        self.assertTrue(form.fields["label"].disabled)
        self.assertTrue(form.fields["settings"].disabled)
