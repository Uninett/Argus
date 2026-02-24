from django.test import TestCase, override_settings
from django.urls import reverse

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import (
    DestinationConfigFactory,
    NotificationProfileFactory,
    TimeslotFactory,
)
from argus.notificationprofile.models import DestinationConfig, Media


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class TestDestinationLoginRequired(TestCase):
    def test_unauthenticated_get_redirects_to_login(self):
        response = self.client.get(reverse("htmx:destination-list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class DestinationViewTestCase(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.client.force_login(user=self.user)
        self.email_media = Media.objects.get(slug="email")


class TestDestinationListView(DestinationViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("htmx:destination-list")

    def test_get_renders_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/destination/destination_list.html")

    def test_context_has_update_forms(self):
        DestinationConfigFactory(
            user=self.user,
            media=self.email_media,
            settings={"email_address": "test@example.com", "synced": False},
        )

        response = self.client.get(self.url)

        forms = response.context["update_forms"]
        self.assertEqual(len(forms), self.user.destinations.count())

    def _get_form_for(self, response, destination):
        return next(f for f in response.context["update_forms"] if f.instance.pk == destination.pk)

    def test_free_destination_has_delete_disabled_false(self):
        destination = DestinationConfigFactory(
            user=self.user,
            media=self.email_media,
            settings={"email_address": "free@example.com", "synced": False},
        )

        response = self.client.get(self.url)

        form = self._get_form_for(response, destination)
        self.assertFalse(form.delete_disabled)

    def test_destination_in_use_has_delete_disabled(self):
        destination = DestinationConfigFactory(
            user=self.user,
            media=self.email_media,
            settings={"email_address": "used@example.com", "synced": False},
        )
        timeslot = TimeslotFactory(user=self.user)
        profile = NotificationProfileFactory(user=self.user, timeslot=timeslot)
        profile.destinations.add(destination)

        response = self.client.get(self.url)

        form = self._get_form_for(response, destination)
        self.assertTrue(form.delete_disabled)
        self.assertIn("used by a notification profile", form.delete_tooltip)

    def test_synced_destination_has_delete_disabled(self):
        destination = DestinationConfigFactory(
            user=self.user,
            media=self.email_media,
            settings={"email_address": "synced@example.com", "synced": True},
        )

        response = self.client.get(self.url)

        form = self._get_form_for(response, destination)
        self.assertTrue(form.delete_disabled)
        self.assertIn("synced from an outside source", form.delete_tooltip)

    def test_only_shows_own_destinations(self):
        other_user = PersonUserFactory()
        DestinationConfigFactory(
            user=other_user,
            media=self.email_media,
            settings={"email_address": "other@example.com", "synced": False},
        )

        response = self.client.get(self.url)

        forms = response.context["update_forms"]
        self.assertTrue(all(f.instance.user == self.user for f in forms))


class TestDestinationCreateView(DestinationViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("htmx:destination-create")

    def test_htmx_get_returns_create_row_partial(self):
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/destination/_destination_create_row.html")

    def test_htmx_valid_post_creates_and_redirects(self):
        count_before = DestinationConfig.objects.filter(user=self.user).count()
        post_data = {
            "destination-media": self.email_media.pk,
            "destination-label": "My Email",
            "destination-settings": "new@example.com",
        }

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Redirect", response.headers)
        self.assertEqual(DestinationConfig.objects.filter(user=self.user).count(), count_before + 1)

    def test_htmx_invalid_post_returns_create_row_with_errors(self):
        post_data = {
            "destination-media": self.email_media.pk,
            "destination-label": "",
            "destination-settings": "",
        }

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/destination/_destination_create_row.html")
        self.assertTrue(response.context["form"].errors)

    def test_form_clean_early_return_when_media_missing(self):
        post_data = {
            "destination-media": "",
            "destination-label": "Test",
            "destination-settings": "test@example.com",
        }

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertIn("media", response.context["form"].errors)


class TestDestinationUpdateView(DestinationViewTestCase):
    def setUp(self):
        super().setUp()
        self.destination = DestinationConfigFactory(
            user=self.user,
            media=self.email_media,
            settings={"email_address": "old@example.com", "synced": False},
        )
        self.url = reverse("htmx:destination-update", kwargs={"pk": self.destination.pk})

    def _build_post_data(self, label="Updated", settings="updated@example.com"):
        prefix = f"destination_{self.destination.pk}"
        return {
            f"{prefix}-media": self.email_media.pk,
            f"{prefix}-label": label,
            f"{prefix}-settings": settings,
        }

    def test_valid_post_saves_and_renders_table_with_success(self):
        response = self.client.post(self.url, data=self._build_post_data())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/destination/_destination_table.html")
        self.assertIn("success_message", response.context)

    def test_valid_post_persists_changes(self):
        self.client.post(self.url, data=self._build_post_data(settings="new@example.com"))

        self.destination.refresh_from_db()
        self.assertEqual(self.destination.settings["email_address"], "new@example.com")

    def test_invalid_post_returns_form_with_errors(self):
        response = self.client.post(self.url, data=self._build_post_data(settings=""))

        self.assertEqual(response.status_code, 200)
        form = next(f for f in response.context["update_forms"] if f.instance.pk == self.destination.pk)
        self.assertTrue(form.errors)

    def test_cannot_update_other_users_destination(self):
        other_user = PersonUserFactory()
        other_dest = DestinationConfigFactory(
            user=other_user,
            media=self.email_media,
            settings={"email_address": "other@example.com", "synced": False},
        )
        url = reverse("htmx:destination-update", kwargs={"pk": other_dest.pk})

        # Post data is irrelevant — the queryset filter rejects before form processing
        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, 404)


class TestDestinationDeleteView(DestinationViewTestCase):
    def setUp(self):
        super().setUp()
        self.destination = DestinationConfigFactory(
            user=self.user,
            media=self.email_media,
            settings={"email_address": "delete@example.com", "synced": False},
        )
        self.url = reverse("htmx:destination-delete", kwargs={"pk": self.destination.pk})

    def test_post_deletes_and_redirects(self):
        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("htmx:destination-list"), fetch_redirect_response=False)
        self.assertFalse(DestinationConfig.objects.filter(pk=self.destination.pk).exists())

    def test_cannot_delete_other_users_destination(self):
        other_user = PersonUserFactory()
        other_dest = DestinationConfigFactory(
            user=other_user,
            media=self.email_media,
            settings={"email_address": "other@example.com", "synced": False},
        )
        url = reverse("htmx:destination-delete", kwargs={"pk": other_dest.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(DestinationConfig.objects.filter(pk=other_dest.pk).exists())

    def test_delete_synced_destination_shows_error(self):
        self.destination.settings["synced"] = True
        self.destination.save()

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("error_msg", response.context)
        self.assertTrue(DestinationConfig.objects.filter(pk=self.destination.pk).exists())

    def test_delete_destination_in_use_shows_error(self):
        timeslot = TimeslotFactory(user=self.user)
        profile = NotificationProfileFactory(user=self.user, timeslot=timeslot)
        profile.destinations.add(self.destination)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("error_msg", response.context)
        self.assertTrue(DestinationConfig.objects.filter(pk=self.destination.pk).exists())
