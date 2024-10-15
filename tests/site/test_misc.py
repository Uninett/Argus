import unittest

from argus.site.views import get_version


class GetVersionTest(unittest.TestCase):

    def test_get_version_never_fails(self):
        version = get_version()
        self.assertTrue(isinstance(version, str))
