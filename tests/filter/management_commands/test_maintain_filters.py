from unittest.mock import patch
from io import StringIO

from django.core.management import call_command, CommandError
from django.test import TestCase

from argus.filter.factories import FilterFactory


class MaintainFiltersTests(TestCase):
    def setUp(self):
        self.open_filter = FilterFactory(filter={"open": True})
        self.closed_filter = FilterFactory(filter={"open": False})
        self.noisy_filter = FilterFactory(filter={"open": None})

    def test_when_golden_path_then_should_minimalize_only_noisy_filters(self):
        out = StringIO()
        original_open = self.open_filter.filter.copy()
        original_closed = self.closed_filter.filter.copy()
        call_command(
            "maintain_filters",
            stdout=out,
        )

        self.noisy_filter.refresh_from_db()
        self.open_filter.refresh_from_db()
        self.closed_filter.refresh_from_db()

        # Strop the noise
        self.assertEqual(self.noisy_filter.filter, {})
        # Don't change the others
        self.assertEqual(self.open_filter.filter, original_open)
        self.assertEqual(self.closed_filter.filter, original_closed)

    def test_when_dry_run_then_should_not_alter_any_filters(self):
        out = StringIO()
        original_open = self.open_filter.filter.copy()
        original_closed = self.closed_filter.filter.copy()
        original_noisy = self.noisy_filter.filter.copy()
        call_command(
            "maintain_filters",
            dry_run=True,
            stdout=out,
        )

        self.noisy_filter.refresh_from_db()
        self.open_filter.refresh_from_db()
        self.closed_filter.refresh_from_db()

        # Don't change anything
        self.assertEqual(self.noisy_filter.filter, original_noisy)
        self.assertEqual(self.open_filter.filter, original_open)
        self.assertEqual(self.closed_filter.filter, original_closed)

    def test_when_not_verbose_then_should_not_output_anything(self):
        out = StringIO()
        call_command(
            "maintain_filters",
            verbosity=0,
            stdout=out,
        )
        self.assertFalse(out.getvalue())

    def test_when_function_not_available_then_do_nothing(self):
        out = StringIO()
        original_open = self.open_filter.filter.copy()
        original_closed = self.closed_filter.filter.copy()
        original_noisy = self.noisy_filter.filter.copy()

        with patch("argus.filter.management.commands.maintain_filters.filter_backend") as module:
            del module.minimalize_filterblob
            with self.assertRaises(CommandError):
                call_command(
                    "maintain_filters",
                    stdout=out,
                )

        self.noisy_filter.refresh_from_db()
        self.open_filter.refresh_from_db()
        self.closed_filter.refresh_from_db()

        # Don't change anything
        self.assertEqual(self.noisy_filter.filter, original_noisy)
        self.assertEqual(self.open_filter.filter, original_open)
        self.assertEqual(self.closed_filter.filter, original_closed)
