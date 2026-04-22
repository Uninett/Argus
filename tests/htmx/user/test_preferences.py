from django.test import TestCase

from argus.htmx.user.factories import ArgusHtmxPreferencesFactory


class TestArgusHtmxPreferencesUpdateContext(TestCase):
    def test_given_deprecated_theme_in_preferences_then_resolves_to_new_name(self):
        prefs = ArgusHtmxPreferencesFactory(preferences={"theme": "sikt"})
        context = prefs.get_context()
        self.assertEqual(context["theme"], "light")

    def test_given_deprecated_dark_theme_in_preferences_then_resolves_to_dark(self):
        prefs = ArgusHtmxPreferencesFactory(preferences={"theme": "sikt-dark"})
        context = prefs.get_context()
        self.assertEqual(context["theme"], "dark")

    def test_given_current_theme_in_preferences_then_passes_through(self):
        prefs = ArgusHtmxPreferencesFactory(preferences={"theme": "argus"})
        context = prefs.get_context()
        self.assertEqual(context["theme"], "argus")
