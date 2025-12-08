from django.test import TestCase
from django.urls import reverse

from argus.auth.factories import PersonUserFactory


class TestUserPreferencesView(TestCase):
    def test_renders_user_preferences_with_expected_context(self):
        user = PersonUserFactory()
        self.client.force_login(user=user)
        response = self.client.get(reverse("htmx:user-preferences"))
        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertIn("htmx/user/preferences_list.html", template_names)
        self.assertIn("forms", response.context)
        self.assertIn("theme_forms", response.context)
        self.assertIn("incident_forms", response.context)
        self.assertIn("columns", response.context)
        self.assertIn("incident_list", response.context)


class TestIncidentTablePreviewView(TestCase):
    def test_incident_table_preview_uses_compact_layout_and_expected_context(self):
        user = PersonUserFactory()
        self.client.force_login(user=user)
        response = self.client.get(reverse("htmx:incident-table-preview"), {"incidents_table_layout": "compact"})
        self.assertEqual(response.status_code, 200)
        template_names = [t.name for t in response.templates]
        self.assertIn("htmx/incident/_unpaged_incident_table.html", template_names)
        self.assertIn("preferences", response.context)
        self.assertIn("columns", response.context)
        self.assertIn("incident_list", response.context)
        table_layout = response.context["preferences"]["argus_htmx"]["incidents_table_layout"]
        self.assertEqual("compact", table_layout)
