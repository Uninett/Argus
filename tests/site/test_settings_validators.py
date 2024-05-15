import unittest

from argus.site.settings._serializers import AppSetting


class AppSettingTests(unittest.TestCase):
    def test_when_app_settings_only_contains_app_name_it_should_validate(self):
        setting = {"app_name": "foo"}
        result = AppSetting(**setting)
        self.assertTrue(result.app_name)
        self.assertFalse(result.urls)
        self.assertFalse(result.context_processors)
