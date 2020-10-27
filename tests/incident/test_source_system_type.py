from django.db import IntegrityError
from django.test import TestCase

from argus.incident.models import SourceSystemType
from argus.incident.serializers import SourceSystemTypeSerializer


class SourceSystemTypeTests(TestCase):
    def test_name_is_always_lowercase_when_creating(self):
        source_type1 = SourceSystemType.objects.create(name="NAV")
        source_type1_expected_name = "nav"
        self.assertEqual(source_type1.name, source_type1_expected_name)
        source_type2 = SourceSystemType.objects.create(name="123")
        self.assertEqual(source_type2.name, "123")
        source_type3 = SourceSystemType.objects.create(name="123Abc")
        self.assertEqual(source_type3.name, "123abc")

    def test_creating_type_with_differently_cased_existing_name_fails(self):
        SourceSystemType.objects.create(name="NAV")
        with self.assertRaises(IntegrityError):
            SourceSystemType.objects.create(name="nAv")

    def test_serializer_validates_name_case(self):
        serializer = SourceSystemTypeSerializer(data={"name": "nav"})
        self.assertTrue(serializer.is_valid())
        serializer = SourceSystemTypeSerializer(data={"name": "NAV"})
        self.assertFalse(serializer.is_valid())
