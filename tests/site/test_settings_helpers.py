import unittest

from argus.site.settings import normalize_url, _add_missing_scheme_to_url


class NormalizeUrlTests(unittest.TestCase):

    def test_add_missing_scheme_if_recoverable(self):
        test_url_80 = "//localhost:80/fgh/ghj/?ghj=gh#fghj"
        fixed_url = _add_missing_scheme_to_url(test_url_80)
        correct_url_80 = "http://localhost:80/fgh/ghj/?ghj=gh#fghj"
        self.assertEqual(fixed_url, correct_url_80)
        test_url_443 = "//localhost:443/fgh/ghj/?ghj=gh#fghj"
        fixed_url = _add_missing_scheme_to_url(test_url_443)
        correct_url_443 = "https://localhost:443/fgh/ghj/?ghj=gh#fghj"
        self.assertEqual(fixed_url, correct_url_443)

    def test_dont_add_missing_scheme_if_not_recoverable(self):
        test_url_noport = "//localhost/fgh/ghj/?ghj=gh#fghj"
        fixed_url = _add_missing_scheme_to_url(test_url_noport)
        self.assertEqual(fixed_url, test_url_noport)
        test_url_unknown_port = "//localhost:5431/fgh/ghj/?ghj=gh#fghj"
        fixed_url = _add_missing_scheme_to_url(test_url_unknown_port)
        self.assertEqual(fixed_url, test_url_unknown_port)

    def test_strip_redundant_ports(self):
        test_url_80 = "http://localhost:80/fgh/ghj/?ghj=gh#fghj"
        fixed_url = normalize_url(test_url_80)
        correct_url_80 = "http://localhost/fgh/ghj/?ghj=gh#fghj"
        self.assertEqual(fixed_url, correct_url_80)
        test_url_443 = "https://localhost:443/fgh/ghj/?ghj=gh#fghj"
        fixed_url = normalize_url(test_url_443)
        correct_url_443 = "https://localhost/fgh/ghj/?ghj=gh#fghj"
        self.assertEqual(fixed_url, correct_url_443)

    def test_dont_strip_unknown_ports(self):
        test_url_unknown_port = "http://localhost:5431/fgh/ghj/?ghj=gh#fghj"
        fixed_url = normalize_url(test_url_unknown_port)
        self.assertEqual(fixed_url, test_url_unknown_port)
