"""Tests that the custom format module provides ISO-style date/time formats.

When USE_L10N was removed (Django 6.0), Django always uses locale-aware
formatting. The custom format module at argus.site.formats.en ensures we
keep ISO-style dates instead of Django's built-in en locale defaults.
"""

import datetime

from django.template import Context, Template
from django.test import TestCase
from django.utils.formats import get_format


SAMPLE_DATETIME = datetime.datetime(2026, 3, 20, 14, 5, 9)


class FormatSpecifierTests(TestCase):
    def test_when_l10n_active_then_datetime_format_is_iso(self):
        assert get_format("DATETIME_FORMAT") == "Y-m-d H:i:s"

    def test_when_l10n_active_then_date_format_is_iso(self):
        assert get_format("DATE_FORMAT") == "Y-m-d"

    def test_when_l10n_active_then_short_datetime_format_is_iso(self):
        assert get_format("SHORT_DATETIME_FORMAT") == "Y-m-d H:i"

    def test_when_l10n_active_then_time_format_is_24h(self):
        assert get_format("TIME_FORMAT") == "H:i:s"


class RenderedDateOutputTests(TestCase):
    def _render(self, format_name):
        template = Template('{{ val|date:"' + format_name + '" }}')
        return template.render(Context({"val": SAMPLE_DATETIME}))

    def test_when_rendering_datetime_format_then_produces_iso_string(self):
        assert self._render("DATETIME_FORMAT") == "2026-03-20 14:05:09"

    def test_when_rendering_date_format_then_produces_iso_string(self):
        assert self._render("DATE_FORMAT") == "2026-03-20"

    def test_when_rendering_short_datetime_format_then_produces_iso_string(self):
        assert self._render("SHORT_DATETIME_FORMAT") == "2026-03-20 14:05"

    def test_when_rendering_time_format_then_produces_24h_string(self):
        assert self._render("TIME_FORMAT") == "14:05:09"
