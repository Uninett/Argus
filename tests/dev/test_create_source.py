from django.core.management import call_command
from django.test import TestCase

from argus.incident.models import SourceSystem
from argus.util.testing import connect_signals, disconnect_signals


class CreateSourceTests(TestCase):
    def setUp(self):
        disconnect_signals()

    def tearDown(self):
        connect_signals()

    def test_create_source_will_create_source(self):
        previous_source_pks = [source.id for source in SourceSystem.objects.all()]
        source_name = "source name"
        call_command("create_source", source_name)

        self.assertTrue(SourceSystem.objects.exclude(id__in=previous_source_pks).filter(type_id="argus").exists())

    def test_create_source_will_create_source_with_set_type(self):
        previous_source_pks = [source.id for source in SourceSystem.objects.all()]
        source_name = "source name"
        source_type = "other"
        call_command("create_source", source_name, source_type=source_type)

        self.assertTrue(SourceSystem.objects.exclude(id__in=previous_source_pks).filter(type_id=source_type).exists())
