from django.test import TestCase

from argus.filter.filterwrapper import SpecialFilterKey
from argus.htmx.incident.filter import IncidentFilterForm, _convert_filterblob
from argus.incident.factories import SourceSystemFactory
from argus.util.testing import disconnect_signals, connect_signals


class TestToFilterblobSpecialFilters(TestCase):
    def setUp(self):
        disconnect_signals()
        SourceSystemFactory(name="testsource")

    def tearDown(self):
        connect_signals()

    def test_when_special_filters_are_selected_then_filterblob_it_should_contain_them_as_booleans(self):
        form = IncidentFilterForm({"special_filters": [SpecialFilterKey.HIDE_CLOSED_ACKED.value]})
        filterblob = form.to_filterblob()
        self.assertTrue(filterblob.get(SpecialFilterKey.HIDE_CLOSED_ACKED.value))

    def test_when_no_special_filters_selected_then_filterblob_it_should_not_contain_special_keys(self):
        form = IncidentFilterForm({})
        filterblob = form.to_filterblob()
        self.assertNotIn(SpecialFilterKey.HIDE_CLOSED_ACKED.value, filterblob)


class TestConvertFilterblobSpecialFilters(TestCase):
    def test_when_filterblob_has_special_filter_booleans_then_it_should_convert_to_list(self):
        filterblob = {SpecialFilterKey.HIDE_CLOSED_ACKED.value: True}
        result = _convert_filterblob(filterblob)
        self.assertIn("special_filters", result)
        self.assertIn(SpecialFilterKey.HIDE_CLOSED_ACKED.value, result["special_filters"])
        # The individual keys should be removed
        self.assertNotIn(SpecialFilterKey.HIDE_CLOSED_ACKED.value, result)

    def test_when_filterblob_has_no_special_filters_then_it_should_not_add_special_filters_key(self):
        filterblob = {"open": True}
        result = _convert_filterblob(filterblob)
        self.assertNotIn("special_filters", result)

    def test_when_filterblob_has_only_one_special_filter_then_it_should_convert_correctly(self):
        filterblob = {SpecialFilterKey.HIDE_CLOSED_ACKED.value: True}
        result = _convert_filterblob(filterblob)
        self.assertEqual(result["special_filters"], [SpecialFilterKey.HIDE_CLOSED_ACKED.value])
