"""Tests for the custom PostgreSQL backend's infinity timestamp handling.

Verifies that PostgreSQL infinity/-infinity timestamps round-trip correctly
through psycopg3 via our custom loaders, returning datetime.max/datetime.min.
"""

from datetime import datetime, timezone

from django.db import connection
from django.test import TestCase


class InfinityTimestampLoaderTests(TestCase):
    """Verify that the custom backend correctly loads infinity timestamps."""

    def test_when_loading_infinity_timestamptz_then_returns_datetime_max(self):
        with connection.cursor() as cur:
            cur.execute("SELECT 'infinity'::timestamptz")
            result = cur.fetchone()[0]
        self.assertEqual(result.replace(tzinfo=None), datetime.max)

    def test_when_loading_negative_infinity_timestamptz_then_returns_datetime_min(self):
        with connection.cursor() as cur:
            cur.execute("SELECT '-infinity'::timestamptz")
            result = cur.fetchone()[0]
        self.assertEqual(result.replace(tzinfo=None), datetime.min)

    def test_when_loading_regular_timestamptz_then_returns_normal_datetime(self):
        expected = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
        with connection.cursor() as cur:
            cur.execute("SELECT '2026-01-15 12:00:00+00'::timestamptz")
            result = cur.fetchone()[0]
        self.assertEqual(result, expected)

    def test_when_loading_infinity_timestamp_then_returns_datetime_max(self):
        with connection.cursor() as cur:
            cur.execute("SELECT 'infinity'::timestamp")
            result = cur.fetchone()[0]
        self.assertEqual(result.replace(tzinfo=None), datetime.max)

    def test_when_loading_negative_infinity_timestamp_then_returns_datetime_min(self):
        with connection.cursor() as cur:
            cur.execute("SELECT '-infinity'::timestamp")
            result = cur.fetchone()[0]
        self.assertEqual(result.replace(tzinfo=None), datetime.min)

    def test_when_inserting_infinity_via_param_then_round_trips(self):
        with connection.cursor() as cur:
            cur.execute("SELECT %s::timestamptz", ["infinity"])
            result = cur.fetchone()[0]
        self.assertEqual(result.replace(tzinfo=None), datetime.max)

    def test_when_inserting_negative_infinity_via_param_then_round_trips(self):
        with connection.cursor() as cur:
            cur.execute("SELECT %s::timestamptz", ["-infinity"])
            result = cur.fetchone()[0]
        self.assertEqual(result.replace(tzinfo=None), datetime.min)

    def test_when_vendor_is_postgresql_then_is_postgres_returns_true(self):
        from argus.incident.fields import DateTimeInfinityField

        self.assertTrue(DateTimeInfinityField.is_postgres(connection))
