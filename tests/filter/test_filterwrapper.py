from random import choice
import unittest
from unittest.mock import Mock

from django.test import tag, override_settings
from django.utils.dateparse import parse_time

from argus.filter.filterwrapper import FilterWrapper
from argus.filter.factories import FilterFactory
from argus.incident.models import Incident, Event


@tag("unittest")
class FilterWrapperTristatesEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A tristate must be one of True, False, None
    # "None" is equivalent to the tristate not being mentioned in the filter at all

    def test_are_tristates_empty_ignores_garbage(self):
        garbage_filter = FilterWrapper({"unknown-state": True})
        result = garbage_filter.are_tristates_empty()
        self.assertTrue(result)

    def test_are_tristates_empty_is_false(self):
        # tristate == None is equivalent to tristate missing from dict
        empty_filter = FilterWrapper({})
        result = empty_filter.are_tristates_empty()
        self.assertTrue(result)
        empty_filter2 = FilterWrapper({"open": None})
        result = empty_filter2.are_tristates_empty()
        self.assertTrue(result)

    @override_settings(ARGUS_FALLBACK_FILTER={"acked": False})
    def test_are_tristates_empty_with_fallback(self):
        from django.conf import settings

        self.assertEqual(
            {"acked": False}, getattr(settings, "ARGUS_FALLBACK_FILTER", {}), "Test hasn't updated settings"
        )
        empty_filter = FilterWrapper({})
        result = empty_filter.are_tristates_empty()
        self.assertFalse(result)

    def test_are_tristates_empty_is_true(self):
        filter = FilterWrapper({"open": False})
        result = filter.are_tristates_empty()
        self.assertFalse(result)
        filter2 = FilterWrapper({"open": True})
        result = filter2.are_tristates_empty()
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
class FilterWrapperMaxlevelEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A maxlevel must be one of the integers in Incident.LEVELS if it is set at all.

    def test_is_maxlevel_empty_is_false(self):
        empty_filter = FilterWrapper({})
        result = empty_filter.is_maxlevel_empty()
        self.assertTrue(result)

    def test_is_maxlevel_empty_is_true(self):
        empty_filter = FilterWrapper({"maxlevel": "whatever"})
        result = empty_filter.is_maxlevel_empty()
        self.assertFalse(result)


@tag("unittest")
class FilterWrapperIncidentFitsMaxlevelTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A maxlevel must be one of the integers in Incident.LEVELS if it is set at all.

    def test_incident_fits_maxlevel_no_maxlevel_set(self):
        incident = Mock()
        empty_filter = FilterWrapper({})
        result = empty_filter.incident_fits_maxlevel(incident)
        self.assertEqual(result, None)

    def test_incident_fits_maxlevel(self):
        incident = Mock()
        level = choice(Incident.LEVELS)
        maxlevel = choice(Incident.LEVELS)
        incident.level = level
        filter = FilterWrapper({"maxlevel": maxlevel})
        result = filter.incident_fits_maxlevel(incident)
        self.assertEqual(result, level <= maxlevel)


@tag("unittest")
class FilterWrapperEventTypeEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # An event type must be one of the types in Event.Type if it is set at all.

    def test_when_filter_is_empty_is_event_types_empty_should_return_true(self):
        empty_filter = FilterWrapper({})
        self.assertTrue(empty_filter.is_event_types_empty())

    def test_when_event_filter_exists_is_event_types_empty_should_return_false(self):
        empty_filter = FilterWrapper({"event_types": ["whatever"]})
        self.assertFalse(empty_filter.is_event_types_empty())


@tag("unittest")
class FilterWrapperIncidentFitsEventTypeTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # An event type must be one of the types in Event.Type if it is set at all.

    def test_when_event_filter_is_empty_any_event_should_fit(self):
        event = Mock()
        empty_filter = FilterWrapper({})
        self.assertEqual(empty_filter.event_fits(event), True)

    def test_when_event_filter_is_set_event_with_matching_type_should_fit(self):
        event = Mock()
        event_type = Event.Type.INCIDENT_CHANGE
        event.type = event_type
        filter = FilterWrapper({"event_types": [event_type]})
        self.assertTrue(filter.event_fits(event))

    def test_when_event_filter_is_set_event_with_not_matching_type_should_not_fit(self):
        event = Mock()
        event_type = Event.Type.INCIDENT_CHANGE
        event.type = event_type
        filter = FilterWrapper({"event_types": [Event.Type.ACKNOWLEDGE]})
        self.assertFalse(filter.event_fits(event))


@tag("unittest")
class FilterWrapperSourceSystemIdsEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A sourceSystemId must be an integer if it is set at all.

    def test_when_filter_is_empty_are_source_system_ids_empty_should_return_true(self):
        empty_filter = FilterWrapper({})
        self.assertTrue(empty_filter.are_source_system_ids_empty())

    def test_when_source_system_ids_is_an_empty_list_are_source_system_ids_empty_should_return_true(self):
        empty_filter = FilterWrapper({"sourceSystemIds": []})
        self.assertTrue(empty_filter.are_source_system_ids_empty())

    def test_when_source_system_ids_filter_exists_are_source_system_ids_empty_should_return_false(self):
        empty_filter = FilterWrapper({"sourceSystemIds": [1]})
        self.assertFalse(empty_filter.are_source_system_ids_empty())


@tag("unittest")
class FilterWrapperTagsEmptyTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A tag must be a string of the format key=value if it is set at all.

    def test_when_filter_is_empty_are_tags_empty_should_return_true(self):
        empty_filter = FilterWrapper({})
        self.assertTrue(empty_filter.are_tags_empty())

    def test_when_tags_is_an_empty_list_are_tags_empty_should_return_true(self):
        empty_filter = FilterWrapper({"tags": []})
        self.assertTrue(empty_filter.are_tags_empty())

    def test_when_tags_filter_exists_are_tags_empty_should_return_false(self):
        empty_filter = FilterWrapper({"tags": ["a=b"]})
        self.assertFalse(empty_filter.are_tags_empty())
