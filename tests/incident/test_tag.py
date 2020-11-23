from django.test import TestCase

from argus.incident.models import Tag


class QuerysetTests(TestCase):
    def test_create_from_tag_if_tagstring_creates_tag(self):
        tagstrings = ("object=1", "object=2", "location=Oslo")
        for tagstring in tagstrings:
            Tag.objects.create_from_tag(tagstring)
        self.assertEqual(Tag.objects.count(), len(tagstrings))

    def test_create_from_tag_if_not_tagstring_raises_error(self):
        with self.assertRaises(ValueError):
            Tag.objects.create_from_tag("")
        self.assertEqual(Tag.objects.count(), 0)

    def test_parse_if_no_tags_returns_empty_list(self):
        result = Tag.objects.parse()
        self.assertEqual(result, [])

    def test_parse_if_tags_and_tags_exist_returns_qs(self):
        tag1 = Tag.objects.create_from_tag("object=1")
        tag2 = Tag.objects.create_from_tag("object=2")
        tag3 = Tag.objects.create_from_tag("location=broomcloset")

        result = Tag.objects.parse("object=1")
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), set(Tag.objects.filter(id=tag1.id)))

        result = Tag.objects.parse("object=1", "object=2")
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), set(Tag.objects.filter(id__in=(tag1.id, tag2.id))))

        result = Tag.objects.parse("object=1", "object=2", "location=broomcloset")
        self.assertEqual(len(result), 2)
