from django.core.management import call_command
from django.test import TestCase

from argus.auth.models import User
from argus.incident.models import SourceSystem, SourceSystemType
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

    def test_create_source_will_use_already_existing_source_system_type(self):
        previous_source_pks = [source.id for source in SourceSystem.objects.all()]
        source_name = "source name"
        source_type_name = "source type name"
        existing_source_type = SourceSystemType.objects.create(name=source_type_name)

        call_command("create_source", source_name, source_type=source_type_name)

        source = SourceSystem.objects.exclude(id__in=previous_source_pks).filter(name=source_name).first()
        self.assertTrue(source)
        self.assertEqual(source.type_id, existing_source_type.name)

    def test_create_source_will_use_already_existing_source_system_type_with_differing_case(self):
        # Source system types are forced to lowercase when saving
        # So we need to test for using the same type with different cases
        previous_source_pks = [source.id for source in SourceSystem.objects.all()]
        source_name = "source name"
        capitalized_source_type_name = "Source Type Name"
        lowercase_source_type_name = capitalized_source_type_name.lower()
        existing_source_type = SourceSystemType.objects.create(name=lowercase_source_type_name)

        call_command("create_source", source_name, source_type=capitalized_source_type_name)

        source = SourceSystem.objects.exclude(id__in=previous_source_pks).filter(name=source_name).first()
        self.assertTrue(source)
        self.assertEqual(source.type_id, existing_source_type.name)

    def test_create_source_will_use_already_existing_source_system(self):
        previous_source_pks = [source.id for source in SourceSystem.objects.all()]
        source_name = "source name"
        source_type_name = "source type name"
        source_user = User.objects.create(username=source_name, is_staff=False, is_superuser=False)
        source_type = SourceSystemType.objects.create(name=source_type_name)
        source = SourceSystem.objects.create(name=source_name, type=source_type, user=source_user)

        call_command("create_source", source_name)

        cli_source = SourceSystem.objects.exclude(id__in=previous_source_pks).filter(name=source_name).first()
        self.assertTrue(cli_source)
        self.assertEqual(cli_source.id, source.id)
