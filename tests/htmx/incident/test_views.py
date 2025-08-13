from unittest import TestCase
from urllib.parse import urlencode

from django.http import QueryDict
from django.test import tag, RequestFactory

from argus.htmx.incident.views import dedupe_querydict, add_param_to_querydict


@tag("unit")
class dedupe_querydict_Test(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_do_nothing_with_empty_request_GET(self):
        request = self.factory.get("")
        result = dedupe_querydict(request.GET)
        self.assertFalse(result)

    def test_do_nothing_with_dupeless_request_GET(self):
        data = {
            "a": "a",
            "b": "bbb",
            "c": 1,
        }
        url = urlencode(data)
        request = self.factory.get("?" + url)
        result = dedupe_querydict(request.GET)
        self.assertEqual(result, request.GET)

    def test_dedupe_duped_request_GET(self):
        data = QueryDict("").copy()
        data.setlist("a", ["a", "a", "a"])
        data._mutable = False

        request = self.factory.get("")
        request.GET = data
        result = dedupe_querydict(request.GET)
        expected = QueryDict("a=a")
        self.assertEqual(result, expected)


@tag("unit")
class add_param_to_querydict_Test(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_do_nothing_with_empty_value(self):
        request = self.factory.get("")
        result = add_param_to_querydict(request.GET, "foo", "")
        self.assertEqual(result, request.GET)

    def test_add_param_if_value(self):
        request = self.factory.get("")
        result = add_param_to_querydict(request.GET, "foo", 0)
        self.assertNotEqual(result, request.GET)
        self.assertIn("foo", result)
        self.assertEqual(result["foo"], "0")
