import unittest
from unittest.mock import Mock

from django.test import tag

from argus.filter.filterwrapper import FilterWrapper, SpecialFilterKey


@tag("unittest")
class FilterWrapperIncidentFitsSpecialFiltersTests(unittest.TestCase):
    def test_when_no_special_filters_are_active_then_returns_None(self):
        fw = FilterWrapper({"open": True})
        incident = Mock()
        result = fw._incident_fits_special_filters(incident)
        self.assertIsNone(result)

    def test_when_hide_closed_acked_is_true_and_incident_is_open_then_returns_True(self):
        fw = FilterWrapper({SpecialFilterKey.HIDE_CLOSED_ACKED: True})
        incident = Mock()
        incident.open = True
        incident.acked = True
        result = fw._incident_fits_special_filters(incident)
        self.assertTrue(result)

    def test_when_hide_closed_acked_is_true_and_incident_is_closed_and_unacked_then_returns_True(self):
        fw = FilterWrapper({SpecialFilterKey.HIDE_CLOSED_ACKED: True})
        incident = Mock()
        incident.open = False
        incident.acked = False
        result = fw._incident_fits_special_filters(incident)
        self.assertTrue(result)

    def test_when_hide_closed_acked_is_true_and_incident_is_closed_and_acked_then_returns_False(self):
        fw = FilterWrapper({SpecialFilterKey.HIDE_CLOSED_ACKED: True})
        incident = Mock()
        incident.open = False
        incident.acked = True
        result = fw._incident_fits_special_filters(incident)
        self.assertFalse(result)

    def test_when_hide_closed_acked_is_false_then_it_should_be_ignored(self):
        fw = FilterWrapper({SpecialFilterKey.HIDE_CLOSED_ACKED: False})
        incident = Mock()
        result = fw._incident_fits_special_filters(incident)
        self.assertIsNone(result)
