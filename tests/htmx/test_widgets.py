import json

from django.test import SimpleTestCase

from argus.htmx.widgets import DropdownRadioSelect


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
