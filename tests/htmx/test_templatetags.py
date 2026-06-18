from unittest import TestCase
from datetime import timedelta

from django.test import tag

from argus.htmx.templatetags.argus_htmx import dictvalue, pretty_timedelta


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


@tag("unit")
class PrettyTimedeltaTest(TestCase):
    def test_pretty_timedelta_when_value_is_None_return_fallback(self):
        result = pretty_timedelta(None, "foo")
        self.assertEqual(result, "foo")

    def test_when_value_is_zero_return_constant_string(self):
        result = pretty_timedelta(timedelta(seconds=0))
        self.assertEqual(result, "0\xa0minutes")

    def test_when_value_is_positive_return_calculated_string(self):
        result = pretty_timedelta(timedelta(seconds=1))
        self.assertEqual(result, "0\xa0minutes")
        result = pretty_timedelta(timedelta(seconds=10))
        self.assertEqual(result, "0\xa0minutes")
        result = pretty_timedelta(timedelta(seconds=100000))
        self.assertEqual(result, "1\xa0day, 3\xa0hours")

    def test_when_value_is_negative_return_0_minutes(self):
        result = pretty_timedelta(timedelta(seconds=-1))
        self.assertEqual(result, "0\xa0minutes")
        result = pretty_timedelta(timedelta(seconds=-10))
        self.assertEqual(result, "0\xa0minutes")
        result = pretty_timedelta(timedelta(seconds=-100000))
        self.assertEqual(result, "0\xa0minutes")
