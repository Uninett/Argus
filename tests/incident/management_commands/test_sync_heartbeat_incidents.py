from unittest.mock import patch
from io import StringIO
import contextlib

from django.core.management import call_command
from django.test import TestCase

from argus.incident.models import get_or_create_default_instances


class TestSyncHeartbeatIncidents(TestCase):
    def setUp(self):
        get_or_create_default_instances()

    def test_when_nothing_to_report_and_not_verbose_then_print_nothing(self):
        # No verbosity flag
        F = StringIO()

        with contextlib.redirect_stdout(F):
            call_command("sync_heartbeat_incidents", verbosity=1)

        output = F.getvalue().strip()
        self.assertFalse(output)

    def test_when_nothing_to_report_and_verbose_then_print_nothing(self):
        # Flag "-v 2"
        F = StringIO()

        with contextlib.redirect_stdout(F):
            call_command("sync_heartbeat_incidents", verbosity=2)

        output = F.getvalue().strip()
        self.assertFalse(output)

    def test_when_something_to_report_but_quiet_print_nothing(self):
        # Flag "-v 0"
        F = StringIO()

        alive_sources = []
        new_incidents = ["golgamfrincham"]
        remaining_incidents = []
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents, remaining_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=0)

        output = F.getvalue()
        self.assertFalse(output)

    def test_when_new_dead_source_incidents_then_print_overview_line(self):
        # No verbosity flag
        F = StringIO()

        alive_sources = []
        new_incidents = ["golgamfrincham"]
        remaining_incidents = []
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents, remaining_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=1)

        output = F.getvalue().strip()
        self.assertEqual(
            output,
            "Heartbeat incidents: Created: 1, Closed: 0, Remaining: 0",
        )

    def test_when_new_dead_source_incidents_and_verbose_then_print_incident_in_addition_to_overview(self):
        # Flag "-v 2"
        F = StringIO()

        alive_sources = []
        new_incidents = ["pollywog"]
        remaining_incidents = []
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents, remaining_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=2)

        output = F.getvalue()
        self.assertEqual(
            output, ("Heartbeat incidents: Created: 1, Closed: 0, Remaining: 0\n\nCreated incidents:\n- pollywog\n")
        )

    def test_when_reanimated_source_then_print_overview_line(self):
        # No verbosity flag
        F = StringIO()

        class FakeSource:
            name = "wui"

        alive_sources = [FakeSource]
        new_incidents = []
        remaining_incidents = []
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents, remaining_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=1)

        output = F.getvalue().strip()
        self.assertEqual(output, "Heartbeat incidents: Created: 0, Closed: 1, Remaining: 0")

    def test_when_reanimated_source_and_verbose_then_print_source_name_in_addition_to_overview(self):
        # Flag "-v 2"
        F = StringIO()

        class FakeSource:
            name = "oopsy"

        alive_sources = [FakeSource]
        new_incidents = []
        remaining_incidents = []
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents, remaining_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=2)

        output = F.getvalue()
        self.assertEqual(
            output, ("Heartbeat incidents: Created: 0, Closed: 1, Remaining: 0\n\nClosed incidents:\n- oopsy\n")
        )
