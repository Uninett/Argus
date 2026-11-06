from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from argus.auth.factories import PersonUserFactory
from argus.incident.models import get_or_create_default_instances
from argus.filter.factories import FilterFactory
from argus.notificationprofile.models import Filter
from argus.plannedmaintenance.models import PlannedMaintenanceTask
from argus.util.datetime_utils import LOCAL_INFINITY
from argus.util.testing import connect_signals, disconnect_signals


class CreateMaintenanceTests(TestCase):
    def setUp(self):
        disconnect_signals()
        self.argus_user, _, _ = get_or_create_default_instances()

        self.filter1 = FilterFactory(user=self.argus_user)
        self.filter2 = FilterFactory(user=self.argus_user)

    def tearDown(self):
        connect_signals()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        call_command(
            "create_maintenance",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    def test_when_given_filter_ids_then_create_task_with_linked_filters(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command("--filter_ids", self.filter1.pk, self.filter2.pk)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(set(pm.filters.all()), {self.filter1, self.filter2})

    def test_when_given_filter_blob_then_create_task_with_linked_newly_created_filter(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]
        filter_blob = '{"maxlevel":2, "name": "New filter"}'

        out, err = self.call_command("--filter_blob", filter_blob)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(set(pm.filters.all()), {Filter.objects.filter(name="New filter").first()})

    def test_when_given_filter_blob_with_invalid_json_then_return_error(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]
        filter_blob = "invalid json"

        out, err = self.call_command("--filter_blob", filter_blob)

        self.assertFalse(out)
        self.assertTrue(err)
        self.assertIn("filter_blob", err)

        self.assertFalse(PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).exists())

    def test_when_given_filter_blob_without_name_then_return_error(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]
        filter_blob = '{"maxlevel":2}'

        out, err = self.call_command("--filter_blob", filter_blob)

        self.assertFalse(out)
        self.assertTrue(err)
        self.assertIn("Cannot create a new filter without a name", err)

        self.assertFalse(PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).exists())

    def test_when_given_no_filter_ids_nor_filter_blob_then_return_error(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command()

        self.assertFalse(out)
        self.assertTrue(err)
        self.assertIn("A planned maintenance task without a filter does nothing", err)

        self.assertFalse(PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).exists())

    def test_when_given_start_time_then_create_task_with_set_start_time(self):
        tomorrow = timezone.now() + timedelta(days=1)
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command("--start_time", str(tomorrow), "--filter_ids", self.filter1.pk)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(pm.start_time, tomorrow)

    def test_when_not_given_start_time_then_create_task_with_start_time_now(self):
        now = timezone.now()
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        with patch("argus.plannedmaintenance.management.commands.create_maintenance.timezone") as tz_mock:
            tz_mock.now.return_value = now
            out, err = self.call_command("--filter_ids", self.filter1.pk)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(pm.start_time, now)

    def test_when_given_end_time_then_create_task_with_set_end_time(self):
        tomorrow = timezone.now() + timedelta(days=1)
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command("--end_time", str(tomorrow), "--filter_ids", self.filter1.pk)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(pm.end_time, tomorrow)

    def test_when_not_given_end_time_then_create_task_with_infinity_end_time(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command("--filter_ids", self.filter1.pk, self.filter2.pk)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(pm.end_time, LOCAL_INFINITY)

    def test_when_given_end_time_before_start_time_then_return_error(self):
        tomorrow = timezone.now() + timedelta(days=1)
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command(
            "--start_time",
            str(tomorrow + timedelta(days=3)),
            "--end_time",
            str(tomorrow),
            "--filter_ids",
            self.filter1.pk,
        )

        self.assertFalse(out)
        self.assertTrue(err)
        self.assertIn("End_time needs to be after start_time", err)

        self.assertFalse(PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).exists())

    def test_when_given_created_by_then_create_task_with_set_user(self):
        user = PersonUserFactory()
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command("--created_by", user.username, "--filter_ids", self.filter1.pk, self.filter2.pk)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(pm.created_by, user)

    def test_when_not_given_created_by_then_create_task_with_argus_user(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command("--filter_ids", self.filter1.pk, self.filter2.pk)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(pm.created_by, self.argus_user)

    def test_when_given_non_existing_user_then_return_error(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command(
            "--created_by", "userdoesnotexist", "--filter_ids", self.filter1.pk, self.filter2.pk
        )

        self.assertFalse(out)
        self.assertTrue(err)
        self.assertIn("created_by: User matching query does not exist.", err)

        self.assertFalse(PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).exists())

    def test_when_given_description_then_create_task_with_set_description(self):
        previous_pm_pks = [pm.id for pm in PlannedMaintenanceTask.objects.all()]

        out, err = self.call_command("--description", "ABC", "--filter_ids", self.filter1.pk, self.filter2.pk)

        self.assertFalse(out)
        self.assertFalse(err)

        pm = PlannedMaintenanceTask.objects.exclude(id__in=previous_pm_pks).first()
        self.assertTrue(pm)
        self.assertEqual(pm.description, "ABC")
