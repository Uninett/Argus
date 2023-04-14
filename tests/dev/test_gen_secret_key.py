from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from argus.util.testing import connect_signals, disconnect_signals


class GenSecretKeyTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "gen_secret_key",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_gen_secret_key_will_output_a_secret_key(self):
        out = self.call_command()

        self.assertEqual(type(out), str)
