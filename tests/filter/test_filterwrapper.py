import unittest
from unittest.mock import Mock

from django.test import tag, override_settings
from django.utils.dateparse import parse_time

from argus.filter.filterwrapper import FilterWrapper, FilterKey
from argus.filter.factories import FilterFactory
from argus.incident.models import Incident, Event


@tag("unittest")
class FilterWrapperFallbackFilterTests(unittest.TestCase):
    @override_settings(ARGUS_FALLBACK_FILTER={"acked": True})
    def test_does_not_meddle_with_actual_settings(self):
        from django.conf import settings

        self.assertEqual(
            {"acked": True}, getattr(settings, "ARGUS_FALLBACK_FILTER", {}), "Test hasn't updated settings"
        )


@tag("unittest")
class FilterWrapperGetFilterValueTests(unittest.TestCase):
    def test_ignores_garbage(self):
        garbage_filter = FilterWrapper({"unknown-state": True})
        result = garbage_filter._get_filter_value("acked")
        self.assertFalse(result)

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": True})
    def test_fallback_filter_fills_in_missing_key(self):
        empty_filter = FilterWrapper({})
        result = empty_filter._get_filter_value("acked")
        self.assertTrue(result)

    @override_settings(ARGUS_FALLBACK_FILTER={"maxlevel": 4})
    def test_fallback_filter_does_not_override_given_key(self):
        filter_ = FilterWrapper({"maxlevel": 3})
        result = filter_._get_filter_value("maxlevel")
        self.assertEqual(result, 3)


@tag("unittest")
class FilterWrapperIsEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A tristate must be one of True, False, None
    # "None" is equivalent to the tristate not being mentioned in the filter at all

    def test_empty_filter_is_empty(self):
        # tristate == None is equivalent to tristate missing from dict
        empty_filter = FilterWrapper({})
        result = empty_filter.is_empty
        self.assertTrue(result)

    def test_falsey_values_is_empty(self):
        empty_filter = FilterWrapper({"open": None})
        result = empty_filter.is_empty
        self.assertTrue(result)

    def test_one_truthy_key_means_not_empty(self):
        filter_ = FilterWrapper({"open": True})
        result = filter_.is_empty
        self.assertFalse(result)


@tag("unittest")
class FilterWrapperIncidentFitsTristatesTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A tristate must be one of True, False, None
    # "None" is equivalent to the tristate not being mentioned in the filter at all

    def test_get_incident_tristate_checks_no_tristates_set(self):
        incident = Mock()
        empty_filter = FilterWrapper({})
        result = empty_filter.get_incident_tristate_checks(incident)
        self.assertEqual(result, {})

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": True})
    def test_get_incident_tristate_checks_no_tristates_set_with_fallback(self):
        incident = Mock()
        # Shouldn't match
        incident.acked = False
        empty_filter = FilterWrapper({})
        result = empty_filter.get_incident_tristate_checks(incident)
        self.assertEqual(result["open"], None)
        self.assertEqual(result["acked"], False)
        self.assertEqual(result["stateful"], None)
        # Should match
        incident.acked = True
        empty_filter = FilterWrapper({})
        result = empty_filter.get_incident_tristate_checks(incident)
        self.assertNotIn(False, result.values())
        self.assertEqual(result["open"], None)
        self.assertEqual(result["acked"], True)
        self.assertEqual(result["stateful"], None)

    def test_get_incident_tristate_checks_is_true(self):
        incident = Mock()
        incident.open = True
        incident.acked = False
        incident.stateful = True
        filter = FilterWrapper({"open": True, "acked": False})
        result = filter.get_incident_tristate_checks(incident)
        self.assertTrue(set(result.values()))  # result not empty
        self.assertEqual(result["open"], True)
        self.assertEqual(result["acked"], True)
        self.assertEqual(result["stateful"], None)

    def test_get_incident_tristate_checks_is_false(self):
        incident = Mock()
        incident.open = True
        incident.acked = False
        incident.stateful = True
        filter = FilterWrapper({"open": False, "acked": False})
        result = filter.get_incident_tristate_checks(incident)
        self.assertIn(False, result.values())
        self.assertEqual(result["open"], False)
        self.assertEqual(result["acked"], True)
        self.assertEqual(result["stateful"], None)

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": True})
    def test_get_incident_tristate_checks_fallback_should_not_override(self):
        incident = Mock()
        # Should match
        incident.acked = False
        filter = FilterWrapper({"acked": False})
        result = filter.get_incident_tristate_checks(incident)
        self.assertNotIn(False, result.values())
        self.assertEqual(result["open"], None)
        self.assertEqual(result["acked"], True)
        self.assertEqual(result["stateful"], None)


@tag("unittest")
class FilterWrapperIncidentFitsMaxlevelTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A maxlevel must be one of the integers in Incident.LEVELS if it is set at all.

    def test_incident_fits_maxlevel_is_None_if_not_mentioned_in_filter(self):
        incident = Mock()
        empty_filter = FilterWrapper({})
        result = empty_filter._incident_fits_maxlevel(incident)
        self.assertEqual(result, None)

    def test_incident_fits_maxlevel_is_True_if_incident_level_is_lte_maxlevel(self):
        incident = Mock()
        level = 1
        maxlevel = 2
        incident.level = level
        filter = FilterWrapper({FilterKey.MAXLEVEL: maxlevel})
        result = filter._incident_fits_maxlevel(incident)
        self.assertTrue(result)
        self.assertEqual(result, level <= maxlevel)

    def test_incident_fits_maxlevel_is_False_if_incident_level_is_gt_maxlevel(self):
        incident = Mock()
        level = 2
        maxlevel = 1
        incident.level = level
        filter = FilterWrapper({FilterKey.MAXLEVEL: maxlevel})
        result = filter._incident_fits_maxlevel(incident)
        self.assertFalse(result)
        self.assertNotEqual(result, level > maxlevel)


@tag("unittest")
class FilterWrapperIncidentFitsEventTypeTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # An event type must be one of the types in Event.Type if it is set at all.

    def test_when_event_filter_is_empty_any_event_should_fit(self):
        event = Mock()
        empty_filter = FilterWrapper({})
        self.assertEqual(empty_filter.event_fits(event), True)
        empty_filter = FilterWrapper({FilterKey.EVENT_TYPES: []})
        self.assertEqual(empty_filter.event_fits(event), True)

    def test_when_event_filter_is_set_event_with_matching_type_should_fit(self):
        event = Mock()
        event_type = Event.Type.INCIDENT_CHANGE
        event.type = event_type
        filter = FilterWrapper({FilterKey.EVENT_TYPES: [event.type]})
        self.assertTrue(filter.event_fits(event))

    def test_when_event_filter_is_set_event_with_not_matching_type_should_not_fit(self):
        event = Mock()
        event_type = Event.Type.INCIDENT_CHANGE
        event.type = event_type
        filter = FilterWrapper({FilterKey.EVENT_TYPES: [Event.Type.ACKNOWLEDGE]})
        self.assertFalse(filter.event_fits(event))
