from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from argus.auth.factories import PersonUserFactory
from argus.incident.factories import create_fake_incident


class TestIncidentTagRendering(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.incident = create_fake_incident(
            tags=[
                "host=web02.example.com",
                "dashboard=https://grafana.example.com/d/abc123/host-overview"
                "?orgId=1&var-host=web02.example.com&from=now-6h&to=now",
            ]
        )

    def test_incident_tags_partial_uses_non_squishing_layout_for_long_values(self):
        html = render_to_string("htmx/incident/cells/_incident_tags.html", {"incident": self.incident})

        self.assertIn("max-w-96", html)
        self.assertIn("whitespace-nowrap", html)
        self.assertIn("break-words", html)
        self.assertNotIn("break-all", html)

    def test_incident_detail_renders_shared_tags_partial(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("htmx:incident-detail", kwargs={"pk": self.incident.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "max-w-96")
        self.assertContains(response, "whitespace-nowrap")
