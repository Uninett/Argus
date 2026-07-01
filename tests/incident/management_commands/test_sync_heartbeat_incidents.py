from unittest.mock import patch
from io import StringIO
import contextlib

from django.core.management import call_command
from django.test import TestCase

from argus.incident.models import get_or_create_default_instances


class TestSyncHeartbeatIncidents(TestCase):
    def setUp(self):
        get_or_create_default_instances()

    def test_when_no_sources_then_print_nothing(self):
        F = StringIO()

        with contextlib.redirect_stdout(F):
            call_command("sync_heartbeat_incidents", verbosity=0)

        output = F.getvalue().strip()
        self.assertFalse(output)

    def test_when_no_sources_and_verbose_then_print_nothing(self):
        F = StringIO()

        call_command("sync_heartbeat_incidents", verbosity=1)

        output = F.getvalue().strip()
        self.assertFalse(output)

    def test_when_new_dead_source_incidents_then_print_two_lines(self):
        F = StringIO()

        alive_sources = []
        new_incidents = ["golgamfrincham"]
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=0)

        output = F.getvalue().strip()
        self.assertTrue(output)
        new, old = output.split("\n")
        self.assertEqual(new, "Created 1 new incidents")
        self.assertEqual(old, "Closed 0 existing incidents")

    def test_when_new_dead_source_incidents_and_verbose_then_print_one_line(self):
        F = StringIO()

        alive_sources = []
        new_incidents = ["pollywog"]
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=1)

        output = F.getvalue().strip()
        self.assertTrue(output)
        self.assertEqual(output, "Created incident pollywog")

    def test_when_reanimated_source_then_print_two_lines(self):
        F = StringIO()

        class FakeSource:
            name = "wui"

        alive_sources = [FakeSource]
        new_incidents = []
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=0)

        output = F.getvalue().strip()
        self.assertTrue(output)
        new, old = output.split("\n")
        self.assertEqual(new, "Created 0 new incidents")
        self.assertEqual(old, "Closed 1 existing incidents")

    def test_when_new_dead_source_incidents_and_verbose_then_print_two_lines(self):
        F = StringIO()

        class FakeSource:
            name = "oopsy"

        alive_sources = [FakeSource]
        new_incidents = []
        with patch(
            "argus.incident.management.commands.sync_heartbeat_incidents.sync_heartbeats_with_heartbeat_incidents",
            return_value=(alive_sources, new_incidents),
        ):
            with contextlib.redirect_stdout(F):
                call_command("sync_heartbeat_incidents", verbosity=1)

        output = F.getvalue().strip()
        self.assertTrue(output)
        self.assertEqual(output, """Closed incident for source "oopsy", it's back""")
