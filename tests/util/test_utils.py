from django.test import TestCase, tag

from argus.util.utils import collection_to_prose


@tag("unit")
class CollectionToProseTest(TestCase):
    def test_empty_collection_returns_empty_string(self):
        result = collection_to_prose([])
        self.assertEqual(result, "")

    def test_single_item_collection_should_str_that_item(self):
        result = collection_to_prose(["a"])
        self.assertEqual(result, "a")

    def test_two_item_collection_should_join_the_items_with_and(self):
        result = collection_to_prose(["a", 1])
        self.assertEqual(result, "a and 1")

    def test_more_than_two_items_should_join_the_items_with_comma_and_and(self):
        collection = ["a", 1, 1.3]
        result = collection_to_prose(collection)
        self.assertTrue(result.endswith(" and 1.3"))
        self.assertEqual(result.count(", "), len(collection) - 2)
