from django.test import TestCase
from .models import Filter

class FilterTestCase(TestCase):
    def setUp(self):
        Filter.objects.create(name="filter1", user=1, string="dette er et filter")

    def test_filter_creation(self):
        """Animals that can speak are correctly identified"""
        filter1 = Filter.objects.get(name="filter1")
        self.assertEqual(filter1.string, 'dette er et filter')
