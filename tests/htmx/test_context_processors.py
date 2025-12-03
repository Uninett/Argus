import unittest

from django.test import RequestFactory

from argus.htmx.context_processors import metadata


class MetadataContextProcessorTest(unittest.TestCase):
    def test_metadata_returns_str_version(self):
        request = RequestFactory().get("/foo")
        version = metadata(request)["version"]
        self.assertIsInstance(version, str)
