from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from rest_framework.authtoken.models import Token

from argus.auth.factories import AdminUserFactory, PersonUserFactory
from argus.incident.factories import (
    SourceSystemFactory,
    SourceSystemTypeFactory,
    StatefulIncidentFactory,
)
from argus.incident.models import SourceSystem, SourceSystemType

User = get_user_model()


@tag("integration")
class SourceSystemListViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()
        self.source = SourceSystemFactory()

    def test_when_not_logged_in_then_redirects(self):
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        self.assertEqual(response.status_code, 302)

    def test_when_regular_user_then_accessible(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        self.assertEqual(response.status_code, 200)

    def test_it_should_show_sources_in_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        self.assertIn(self.source, response.context["object_list"])

    def test_it_should_annotate_incident_count(self):
        StatefulIncidentFactory(source=self.source)
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        source = response.context["object_list"].get(pk=self.source.pk)
        self.assertEqual(source.incident_count, 1)

    def test_it_should_set_page_title(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        self.assertEqual(response.context["page_title"], "Sources")

    def test_it_should_set_active_tab_to_sources(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        self.assertEqual(response.context["active_tab"], "sources")

    def test_given_no_token_then_status_is_missing(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        source = next(s for s in response.context["object_list"] if s.pk == self.source.pk)
        self.assertEqual(source.token_status, "missing")

    def test_given_valid_token_then_status_is_valid(self):
        Token.objects.create(user=self.source.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        source = next(s for s in response.context["object_list"] if s.pk == self.source.pk)
        self.assertEqual(source.token_status, "valid")

    def test_given_expired_token_then_status_is_expired(self):
        token = Token.objects.create(user=self.source.user)
        token.created = timezone.now() - timedelta(days=365)
        token.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-list"))
        source = next(s for s in response.context["object_list"] if s.pk == self.source.pk)
        self.assertEqual(source.token_status, "expired")


@tag("integration")
class SourceSystemCreateViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()
        self.source_type = SourceSystemTypeFactory()

    def test_when_not_staff_then_forbidden(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-create"))
        self.assertEqual(response.status_code, 403)

    def test_when_staff_then_accessible(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:sourcesystem-create"))
        self.assertEqual(response.status_code, 200)

    def test_when_posting_valid_data_it_should_create_source_and_user(self):
        self.client.force_login(self.staff_user)
        user_count = User.objects.count()
        response = self.client.post(
            reverse("htmx:sourcesystem-create"),
            {"name": "new-source", "type": self.source_type.pk, "base_url": "https://example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SourceSystem.objects.filter(name="new-source").exists())
        self.assertEqual(User.objects.count(), user_count + 1)

    def test_when_creating_it_should_redirect_to_list(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("htmx:sourcesystem-create"),
            {"name": "new-source", "type": self.source_type.pk},
        )
        self.assertRedirects(response, reverse("htmx:sourcesystem-list"))


@tag("integration")
class SourceSystemUpdateViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()
        self.source = SourceSystemFactory()

    def test_when_not_staff_then_forbidden(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystem-update", kwargs={"pk": self.source.pk}))
        self.assertEqual(response.status_code, 403)

    def test_when_staff_then_accessible(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:sourcesystem-update", kwargs={"pk": self.source.pk}))
        self.assertEqual(response.status_code, 200)

    def test_when_posting_it_should_update_name(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("htmx:sourcesystem-update", kwargs={"pk": self.source.pk}),
            {"name": "updated-name", "base_url": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.source.refresh_from_db()
        self.assertEqual(self.source.name, "updated-name")

    def test_it_should_not_expose_type_field(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:sourcesystem-update", kwargs={"pk": self.source.pk}))
        form = response.context["form"]
        self.assertNotIn("type", form.fields)

    def test_it_should_not_expose_user_field(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:sourcesystem-update", kwargs={"pk": self.source.pk}))
        form = response.context["form"]
        self.assertNotIn("user", form.fields)


@tag("integration")
class SourceSystemDeleteViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()
        self.source = SourceSystemFactory()

    def test_when_not_staff_then_forbidden(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("htmx:sourcesystem-delete", kwargs={"pk": self.source.pk}))
        self.assertEqual(response.status_code, 403)

    def test_when_deleting_it_should_remove_source_and_user(self):
        self.client.force_login(self.staff_user)
        source_user = self.source.user
        response = self.client.post(reverse("htmx:sourcesystem-delete", kwargs={"pk": self.source.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SourceSystem.objects.filter(pk=self.source.pk).exists())
        self.assertFalse(User.objects.filter(pk=source_user.pk).exists())

    def test_given_source_with_incidents_when_deleting_it_should_show_error(self):
        StatefulIncidentFactory(source=self.source)
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("htmx:sourcesystem-delete", kwargs={"pk": self.source.pk}),
            follow=True,
        )
        self.assertTrue(SourceSystem.objects.filter(pk=self.source.pk).exists())
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Cannot delete", str(messages[0]))


@tag("integration")
class SourceSystemTypeListViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()
        self.source_type = SourceSystemTypeFactory()

    def test_when_not_logged_in_then_redirects(self):
        response = self.client.get(reverse("htmx:sourcesystemtype-list"))
        self.assertEqual(response.status_code, 302)

    def test_when_regular_user_then_accessible(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystemtype-list"))
        self.assertEqual(response.status_code, 200)

    def test_it_should_annotate_source_count(self):
        SourceSystemFactory(type=self.source_type)
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystemtype-list"))
        source_type = response.context["object_list"].get(pk=self.source_type.pk)
        self.assertEqual(source_type.source_count, 1)

    def test_it_should_set_active_tab_to_types(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystemtype-list"))
        self.assertEqual(response.context["active_tab"], "types")


@tag("integration")
class SourceSystemTypeCreateViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()

    def test_when_not_staff_then_forbidden(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:sourcesystemtype-create"))
        self.assertEqual(response.status_code, 403)

    def test_when_staff_then_accessible(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:sourcesystemtype-create"))
        self.assertEqual(response.status_code, 200)

    def test_when_posting_it_should_create_type(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("htmx:sourcesystemtype-create"), {"name": "newtype"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SourceSystemType.objects.filter(name="newtype").exists())

    def test_when_posting_uppercase_name_then_validation_fails(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("htmx:sourcesystemtype-create"), {"name": "MyType"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SourceSystemType.objects.filter(name="mytype").exists())


@tag("integration")
class SourceSystemTypeDeleteViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()
        self.source_type = SourceSystemTypeFactory()

    def test_when_not_staff_then_forbidden(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("htmx:sourcesystemtype-delete", kwargs={"pk": self.source_type.pk}))
        self.assertEqual(response.status_code, 403)

    def test_when_deleting_it_should_remove_type(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("htmx:sourcesystemtype-delete", kwargs={"pk": self.source_type.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SourceSystemType.objects.filter(pk=self.source_type.pk).exists())

    def test_given_type_with_sources_when_deleting_it_should_show_error(self):
        SourceSystemFactory(type=self.source_type)
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse("htmx:sourcesystemtype-delete", kwargs={"pk": self.source_type.pk}),
            follow=True,
        )
        self.assertTrue(SourceSystemType.objects.filter(pk=self.source_type.pk).exists())
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("Cannot delete", str(messages[0]))
