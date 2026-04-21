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

    def test_when_under_maintenance_is_true_and_incident_has_active_task_then_returns_True(self):
        fw = FilterWrapper({SpecialFilterKey.UNDER_MAINTENANCE: True})
        incident = Mock()
        incident.planned_maintenance_tasks.current.return_value.exists.return_value = True
        result = fw._incident_fits_special_filters(incident)
        self.assertTrue(result)

    def test_when_under_maintenance_is_true_and_incident_has_no_active_task_then_returns_False(self):
        fw = FilterWrapper({SpecialFilterKey.UNDER_MAINTENANCE: True})
        incident = Mock()
        incident.planned_maintenance_tasks.current.return_value.exists.return_value = False
        result = fw._incident_fits_special_filters(incident)
        self.assertFalse(result)

    def test_when_both_special_filters_active_and_both_pass_then_returns_True(self):
        fw = FilterWrapper(
            {
                SpecialFilterKey.HIDE_CLOSED_ACKED: True,
                SpecialFilterKey.UNDER_MAINTENANCE: True,
            }
        )
        incident = Mock()
        incident.open = True
        incident.acked = False
        incident.planned_maintenance_tasks.current.return_value.exists.return_value = True
        result = fw._incident_fits_special_filters(incident)
        self.assertTrue(result)

    def test_when_both_special_filters_active_and_one_fails_then_returns_False(self):
        fw = FilterWrapper(
            {
                SpecialFilterKey.HIDE_CLOSED_ACKED: True,
                SpecialFilterKey.UNDER_MAINTENANCE: True,
            }
        )
        incident = Mock()
        incident.open = False
        incident.acked = True
        incident.planned_maintenance_tasks.current.return_value.exists.return_value = True
        result = fw._incident_fits_special_filters(incident)
        self.assertFalse(result)

    def test_when_hide_closed_acked_is_false_then_it_should_be_ignored(self):
        fw = FilterWrapper({SpecialFilterKey.HIDE_CLOSED_ACKED: False})
        incident = Mock()
        result = fw._incident_fits_special_filters(incident)
        self.assertIsNone(result)

    def test_when_under_maintenance_is_false_then_it_should_be_ignored(self):
        fw = FilterWrapper({SpecialFilterKey.UNDER_MAINTENANCE: False})
        incident = Mock()
        result = fw._incident_fits_special_filters(incident)
        self.assertIsNone(result)
