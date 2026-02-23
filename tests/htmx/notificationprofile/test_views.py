from django.test import TestCase, override_settings
from django.urls import reverse

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import (
    NotificationProfileFactory,
    TimeslotFactory,
)
from argus.notificationprofile.models import Filter


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class NotificationProfileViewTestCase(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.client.force_login(user=self.user)


class TestNotificationProfileListView(NotificationProfileViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("htmx:notificationprofile-list")

    def test_it_should_have_active_tab_profiles_in_context(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "profiles")

    def test_it_should_have_page_title_in_context(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_title"], "Profiles")

    def test_when_get_it_should_list_profiles(self):
        timeslot = TimeslotFactory(user=self.user)
        NotificationProfileFactory(user=self.user, timeslot=timeslot)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["object_list"]), 1)


class TestNotificationProfileDetailView(NotificationProfileViewTestCase):
    def setUp(self):
        super().setUp()
        timeslot = TimeslotFactory(user=self.user)
        self.profile = NotificationProfileFactory(user=self.user, timeslot=timeslot)
        self.url = reverse("htmx:notificationprofile-detail", kwargs={"pk": self.profile.pk})

    def test_when_htmx_get_it_should_return_card_partial(self):
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/notificationprofile/_notificationprofile_card.html")

    def test_when_non_htmx_get_it_should_redirect_to_update(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            reverse("htmx:notificationprofile-update", kwargs={"pk": self.profile.pk}),
            fetch_redirect_response=False,
        )


class TestNotificationProfileCreateView(NotificationProfileViewTestCase):
    def setUp(self):
        super().setUp()
        self.timeslot = TimeslotFactory(user=self.user)
        self.filter = Filter.objects.create(user=self.user, name="Test Filter", filter={})
        self.url = reverse("htmx:notificationprofile-create")

    def _build_post_data(self, **overrides):
        data = {
            "name": "Test Profile",
            "timeslot": self.timeslot.pk,
            "filters": [self.filter.pk],
            "destinations": [],
            "active": "on",
        }
        data.update(overrides)
        return data

    def test_when_get_it_should_render_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_when_htmx_get_it_should_return_form_partial(self):
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/notificationprofile/_notificationprofile_form.html")
        self.assertTrue(response.context["is_create"])

    def test_when_valid_post_it_should_redirect_to_list(self):
        response = self.client.post(self.url, data=self._build_post_data())

        self.assertRedirects(response, reverse("htmx:notificationprofile-list"), fetch_redirect_response=False)

    def test_when_htmx_valid_post_it_should_redirect_via_hx_redirect(self):
        response = self.client.post(self.url, data=self._build_post_data(), HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Redirect", response.headers)


class TestNotificationProfileUpdateView(NotificationProfileViewTestCase):
    def setUp(self):
        super().setUp()
        self.timeslot = TimeslotFactory(user=self.user)
        self.filter = Filter.objects.create(user=self.user, name="Test Filter", filter={})
        self.profile = NotificationProfileFactory(user=self.user, timeslot=self.timeslot, name="Test Profile")
        self.profile.filters.add(self.filter)
        self.url = reverse("htmx:notificationprofile-update", kwargs={"pk": self.profile.pk})

    def test_when_get_it_should_render_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def _build_post_data(self, **overrides):
        prefix = f"npf{self.profile.pk}"
        data = {
            f"{prefix}-name": self.profile.name,
            f"{prefix}-timeslot": self.timeslot.pk,
            f"{prefix}-filters": [self.filter.pk],
            f"{prefix}-destinations": [],
            f"{prefix}-active": "on",
        }
        data.update(overrides)
        return data

    def test_when_htmx_valid_post_it_should_persist_and_render_success(self):
        prefix = f"npf{self.profile.pk}"
        post_data = self._build_post_data(**{f"{prefix}-name": "Updated Name"})

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.name, "Updated Name")
        self.assertIn("success_message", response.context)

    def test_when_htmx_invalid_post_it_should_return_form_content_partial_with_errors(self):
        prefix = f"npf{self.profile.pk}"
        post_data = self._build_post_data(**{f"{prefix}-timeslot": ""})
        del post_data[f"{prefix}-active"]

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/notificationprofile/_notificationprofile_form_content.html")
        self.assertTrue(response.context["form"].errors)

    def test_when_valid_post_it_should_redirect_to_list(self):
        post_data = self._build_post_data()

        response = self.client.post(self.url, data=post_data)

        self.assertRedirects(response, reverse("htmx:notificationprofile-list"), fetch_redirect_response=False)
