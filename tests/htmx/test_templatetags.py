from unittest import TestCase

from django.test import tag

from argus.htmx.templatetags.argus_htmx import dictvalue


@tag("unit")
class DictvalueTests(TestCase):
    def test_get_value_from_dict_golden_path(self):
        testdict = {1: 1, 2: 2}
        self.assertEqual(dictvalue(testdict, 1), 1)

    def test_get_value_from_dict_when_key_is_missing_returns_None(self):
        testdict = {}
        self.assertIsNone(dictvalue(testdict, 1))

    def test_get_value_from_dict_when_key_is_missing_and_default_is_set_returns_default(self):
        testdict = {}
        self.assertEqual(dictvalue(testdict, 1, "boo"), "boo")
