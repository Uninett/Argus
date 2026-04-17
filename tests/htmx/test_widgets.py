import json
import unittest

from django.test import SimpleTestCase, tag

from argus.htmx.widgets import ButtonDropdownMultiSelect, DropdownRadioSelect


class DropdownRadioSelectTest(SimpleTestCase):
    def test_given_badge_classes_when_get_context_then_includes_badge_classes(self):
        badge_classes = {"1": "text-error", "2": "text-success"}
        widget = DropdownRadioSelect(badge_classes=badge_classes, choices=[("1", "A"), ("2", "B")])
        context = widget.get_context("test", "1", {})
        self.assertEqual(context["widget"]["badge_classes"], badge_classes)

    def test_given_badge_classes_when_get_context_then_includes_json_serialized(self):
        badge_classes = {"1": "text-error", "2": "text-success"}
        widget = DropdownRadioSelect(badge_classes=badge_classes, choices=[("1", "A"), ("2", "B")])
        context = widget.get_context("test", "1", {})
        self.assertEqual(json.loads(context["widget"]["badge_classes_json"]), badge_classes)

    def test_given_no_badge_classes_when_get_context_then_defaults_to_empty(self):
        widget = DropdownRadioSelect(choices=[("1", "A")])
        context = widget.get_context("test", "1", {})
        self.assertEqual(context["widget"]["badge_classes"], {})
        self.assertEqual(context["widget"]["badge_classes_json"], "{}")


class StubButtonDropdownMultiSelect(ButtonDropdownMultiSelect):
    """Subclass that stubs optgroups to avoid needing real form field choices."""

    def __init__(self, options, **kwargs):
        super().__init__(partial_get="/fake-url/", **kwargs)
        self._stub_options = options

    def optgroups(self, name, value, attrs=None):
        """Return a single group with the stubbed options."""
        return [("", self._stub_options, 0)]


@tag("unittest")
class ButtonDropdownMultiSelectSelectedCountTests(unittest.TestCase):
    def test_selected_count_returns_zero_when_no_options_are_selected(self):
        options = [
            {"value": "a", "selected": False},
            {"value": "b", "selected": False},
        ]
        widget = StubButtonDropdownMultiSelect(options)
        count = widget.selected_count("test", ["a", "b"], {})
        self.assertEqual(count, 0)

    def test_selected_count_returns_correct_count_when_some_options_are_selected(self):
        options = [
            {"value": "a", "selected": True},
            {"value": "b", "selected": False},
            {"value": "c", "selected": True},
        ]
        widget = StubButtonDropdownMultiSelect(options)
        count = widget.selected_count("test", ["a", "b", "c"], {})
        self.assertEqual(count, 2)

    def test_selected_count_returns_correct_count_when_all_options_are_selected(self):
        options = [
            {"value": "a", "selected": True},
            {"value": "b", "selected": True},
        ]
        widget = StubButtonDropdownMultiSelect(options)
        count = widget.selected_count("test", ["a", "b"], {})
        self.assertEqual(count, 2)

    def test_selected_count_returns_zero_when_no_options(self):
        widget = StubButtonDropdownMultiSelect([])
        count = widget.selected_count("test", [], {})
        self.assertEqual(count, 0)


@tag("unittest")
class ButtonDropdownMultiSelectGetContextTests(unittest.TestCase):
    def test_get_context_it_should_include_selected_count(self):
        options = [
            {"value": "a", "selected": True},
            {"value": "b", "selected": False},
        ]
        widget = StubButtonDropdownMultiSelect(options, choices=[("a", "A"), ("b", "B")])
        context = widget.get_context("test", ["a"], {})
        self.assertIn("selected_count", context["widget"])
        self.assertEqual(context["widget"]["selected_count"], 1)

    def test_get_context_has_selected_is_true_when_count_is_positive(self):
        options = [
            {"value": "a", "selected": True},
        ]
        widget = StubButtonDropdownMultiSelect(options, choices=[("a", "A")])
        context = widget.get_context("test", ["a"], {})
        self.assertTrue(context["widget"]["has_selected"])

    def test_get_context_has_selected_is_false_when_count_is_zero(self):
        options = [
            {"value": "a", "selected": False},
        ]
        widget = StubButtonDropdownMultiSelect(options, choices=[("a", "A")])
        context = widget.get_context("test", [], {})
        self.assertFalse(context["widget"]["has_selected"])
        self.assertEqual(context["widget"]["selected_count"], 0)
