from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from argus.incident.factories import StatefulIncidentFactory, SourceSystemFactory
from argus.incident.admin import IncidentAdmin


class IncidentDetailsUrlTestCase(TestCase):
    def setUp(self):
        self.source_no_base_url = SourceSystemFactory.build(base_url="")
        self.base_url = "https://someticketsystem.example.org"
        self.source_has_base_url = SourceSystemFactory.build(base_url=self.base_url)

    def test_pp_details_url_empty_string(self):
        detail_url = ""
        incident = StatefulIncidentFactory.build(source=self.source_no_base_url, details_url=detail_url)
        self.assertEqual(incident.pp_details_url(), detail_url)

    def test_pp_details_url_relative_url(self):
        detail_url = "foo"
        incident = StatefulIncidentFactory.build(source=self.source_no_base_url, details_url=detail_url)
        self.assertEqual(incident.pp_details_url(), detail_url)

    def test_pp_details_url_has_base_url_empty_string(self):
        detail_url = ""
        incident = StatefulIncidentFactory.build(source=self.source_has_base_url, details_url=detail_url)
        self.assertEqual(incident.pp_details_url(), detail_url)

    def test_pp_details_url_has_base_url_absolute_url(self):
        detail_url = "foo"
        incident = StatefulIncidentFactory.build(source=self.source_has_base_url, details_url=detail_url)
        self.assertTrue(incident.pp_details_url().startswith(self.base_url))
        self.assertTrue(incident.pp_details_url().endswith(detail_url))


class AdminIncidentDetailsUrlTestCase(TestCase):
    def setUp(self):
        self.source_no_base_url = SourceSystemFactory.build(base_url="")
        self.base_url = "https://someticketsystem.example.org"
        self.source_has_base_url = SourceSystemFactory.build(base_url=self.base_url)

    def test_get_details_url_is_link_if_base_url_and_details_url(self):
        detail_url = "foo"
        incident = StatefulIncidentFactory.build(source=self.source_has_base_url, details_url=detail_url)
        incident_admin = IncidentAdmin(incident._meta.model, AdminSite())
        result = incident_admin.get_details_url(incident)
        self.assertTrue(result.startswith(f'<a href="{self.base_url}'))
