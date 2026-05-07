import logging
from unittest import TestCase

from django.test import tag


@tag("unit")
class TraceLogTests(TestCase):
    def test_logging_with_level_TRACE_should_not_trigger_any_errors(self):
        LOG = logging.getLogger(__name__)
        message = "this is a test"
        with self.assertLogs(logger=__name__, level="TRACE") as cm:
            LOG.trace(message)
            self.assertEqual(cm.output, [f"TRACE:tests.test_logging_utils:{message}"])
