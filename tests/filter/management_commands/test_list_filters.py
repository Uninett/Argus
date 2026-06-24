from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from argus.filter.factories import FilterFactory
from argus.filter.serializers import FilterSerializer
from argus.notificationprofile.models import Filter
from argus.util.testing import connect_signals, disconnect_signals


class ListFiltersTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.open_filter = FilterFactory(filter={"open": True})
        self.closed_filter = FilterFactory(filter={"open": False})

    def tearDown(self):
        connect_signals()

    def test_list_filters_will_list_all_filters(self):
        out = StringIO()
        call_command(
            "list_filters",
            stdout=out,
        )

        serializer_data = FilterSerializer(
            Filter.objects.filter(id__in=[self.open_filter.pk, self.closed_filter.pk]), many=True
        ).data

        self.assertEqual(out.getvalue(), f"{serializer_data}\n")

    def test_list_filters_will_list_specific_filter_by_pk(self):
        out = StringIO()
        call_command(
            "list_filters",
            pk=self.open_filter.pk,
            stdout=out,
        )

        serializer_data = FilterSerializer(Filter.objects.filter(id=self.open_filter.pk), many=True).data

        self.assertEqual(out.getvalue(), f"{serializer_data}\n")

    def test_list_filters_will_list_specific_filter_by_name(self):
        out = StringIO()
        call_command(
            "list_filters",
            name=self.closed_filter.name,
            stdout=out,
        )

        serializer_data = FilterSerializer(Filter.objects.filter(id=self.closed_filter.pk), many=True).data

        self.assertEqual(out.getvalue(), f"{serializer_data}\n")

    def test_list_filters_will_fail_with_pk_and_name_given(self):
        with self.assertRaises(CommandError):
            call_command(
                "list_filters",
                f"--pk={self.open_filter.pk}",
                f"--name={self.open_filter.name}",
                stdout=None,
                stderr=None,
            )
