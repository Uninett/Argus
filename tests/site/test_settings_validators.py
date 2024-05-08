import unittest

from argus.site.settings._serializers import AppSetting


class AppSettingTests(unittest.TestCase):
    def test_just_app_in_setting_should_validate(self):
        setting = {"app_name": "foo"}
        result = AppSetting(**setting)
        self.assertTrue(result.app_name)
        self.assertFalse(result.urls)
        self.assertFalse(result.context_processors)
