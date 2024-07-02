import unittest
from unittest.mock import Mock

from django.test import override_settings
from django.test import tag

from argus.filter.filterwrapper import FilterKey
from argus.filter.filterwrapper import FilterWrapper
from argus.incident.models import Event


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
class FilterWrapperIncidentFitsTristateTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A tristate must be one of True, False, None
    # "None" is equivalent to the tristate not being mentioned in the filter at all

    def test_incident_fits_tristate_is_None_for_non_tristates_filters(self):
        incident = Mock()
        empty_filter = FilterWrapper({FilterKey.MAXLEVEL: 2})
        result = empty_filter._incident_fits_tristate(incident, FilterKey.MAXLEVEL)
        self.assertEqual(result, None)

    def test_incident_fits_tristate_is_None_if_not_mentioned_in_filter(self):
        incident = Mock()
        incident.open = True
        filter_ = FilterWrapper({"blbl": True})
        result = filter_._incident_fits_tristate(incident, FilterKey.OPEN)
        self.assertEqual(result, None)

    def test_incident_fits_tristate_is_True_if_True_in_filter_and_incident_tristate_is_True(self):
        incident = Mock()
        incident.acked = True
        filter_ = FilterWrapper({FilterKey.ACKED: True})
        result = filter_._incident_fits_tristate(incident, FilterKey.ACKED)
        self.assertTrue(result)

    def test_incident_fits_tristate_is_False_if_False_in_filter_and_incident_tristate_is_True(self):
        incident = Mock()
        incident.stateful = True
        filter_ = FilterWrapper({FilterKey.STATEFUL: False})
        result = filter_._incident_fits_tristate(incident, FilterKey.STATEFUL)
        self.assertFalse(result)

    def test_incident_fits_tristate_is_False_if_True_in_filter_and_incident_tristate_is_False(self):
        incident = Mock()
        incident.stateful = False
        filter_ = FilterWrapper({FilterKey.STATEFUL: True})
        result = filter_._incident_fits_tristate(incident, FilterKey.STATEFUL)
        self.assertFalse(result)


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
        self.assertEqual(result, level < maxlevel)
        level = 2
        maxlevel = 2
        incident.level = level
        filter = FilterWrapper({FilterKey.MAXLEVEL: maxlevel})
        result = filter._incident_fits_maxlevel(incident)
        self.assertEqual(result, level == maxlevel)

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
class FilterWrapperIncidentFitsSourceSystemTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A maxlevel must be one of the integers in Incident.LEVELS if it is set at all.

    def test_incident_fits_source_system_is_None_if_not_mentioned_in_filter(self):
        incident = Mock()
        incident.source = True
        empty_filter = FilterWrapper({})
        result = empty_filter._incident_fits_source_system(incident)
        self.assertEqual(result, None)

    def test_incident_fits_source_system_is_True_if_incident_source_system_is_the_same_as_filter_source_system(self):
        incident = Mock()
        source = Mock()
        source.id = 1
        incident.source = source
        filter = FilterWrapper({FilterKey.SOURCE_SYSTEM_IDS: [source.id, 2]})
        result = filter._incident_fits_source_system(incident)
        self.assertTrue(result)

    def test_incident_fits_source_system_is_False_if_incident_source_system_is_not_in_filter_source_system(self):
        incident = Mock()
        source = Mock()
        source.id = 1
        incident.source = source
        filter = FilterWrapper({FilterKey.SOURCE_SYSTEM_IDS: [4]})
        result = filter._incident_fits_source_system(incident)
        self.assertFalse(result)


@tag("unittest")
class FilterWrapperIncidentFitsTagsTests(unittest.TestCase):
    # Validation is handled before the data gets to FilterWrapper
    # A maxlevel must be one of the integers in Incident.LEVELS if it is set at all.

    def test_incident_fits_tags_is_None_if_not_mentioned_in_filter(self):
        incident = Mock()
        empty_filter = FilterWrapper({})
        result = empty_filter._incident_fits_tags(incident)
        self.assertEqual(result, None)

    def test_incident_fits_tags_is_False_if_no_incident_tags(self):
        incident = Mock()
        incident.deprecated_tags = []
        filter = FilterWrapper({FilterKey.TAGS: ["a=b"]})
        result = filter._incident_fits_tags(incident)
        self.assertFalse(result)

    def test_incident_fits_tags_is_True_if_incident_tags_is_in_filter_tags(self):
        incident = Mock()
        tag1 = Mock()
        tag1.representation = "b=c"
        tag2 = Mock()
        tag2.representation = "e=f"
        incident.deprecated_tags = [tag2, tag1]
        filter = FilterWrapper({FilterKey.TAGS: ["b=c", "e=f"]})
        result = filter._incident_fits_tags(incident)
        self.assertTrue(result)

    def test_incident_fits_tags_is_False_if_incident_tags_is_not_in_filter_tags(self):
        incident = Mock()
        tag = Mock()
        tag.representation = "e=f"
        incident.deprecated_tags = [tag]
        filter = FilterWrapper({FilterKey.TAGS: ["a=b"]})
        result = filter._incident_fits_tags(incident)
        self.assertFalse(result)


@tag("unittest")
class FilterWrapperEventFitsEventTypeTests(unittest.TestCase):
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
