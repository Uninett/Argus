from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import TimeslotFactory, TimeRecurrenceFactory


class TimeslotViewTestCase(TestCase):
    """Base test case with common setup for timeslot views."""

    def setUp(self):
        self.user = PersonUserFactory()
        self.client.force_login(user=self.user)


class TestTimeslotUpdateView(TimeslotViewTestCase):
    def setUp(self):
        super().setUp()
        self.timeslot = TimeslotFactory(user=self.user)
        self.recurrence = TimeRecurrenceFactory(timeslot=self.timeslot)
        self.url = reverse("htmx:timeslot-update", kwargs={"pk": self.timeslot.pk})

    def test_get_renders_form_with_formset(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("formset", response.context)

    def test_deleting_all_recurrences_shows_warning(self):
        post_data = _build_timeslot_post_data(self.timeslot, [self.recurrence], delete_indices=[0])

        response = self.client.post(self.url, data=post_data)

        self.assertRedirects(response, reverse("htmx:timeslot-list"), fetch_redirect_response=False)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, "warning")
        self.assertIn("no time recurrences", str(messages[0]))

    def test_missing_required_field_shows_error(self):
        post_data = _build_timeslot_post_data(self.timeslot, [self.recurrence])
        formset_prefix = f"timerecurrenceform-{self.timeslot.pk}"
        post_data[f"{formset_prefix}-0-start"] = ""

        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["formset"].errors)

    def test_start_time_must_be_before_end_time(self):
        post_data = _build_timeslot_post_data(self.timeslot, [self.recurrence])
        formset_prefix = f"timerecurrenceform-{self.timeslot.pk}"
        post_data[f"{formset_prefix}-0-start"] = "17:00"
        post_data[f"{formset_prefix}-0-end"] = "08:00"

        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 200)
        formset = response.context["formset"]
        self.assertIn("start", formset.errors[0])
        self.assertIn("before", str(formset.errors[0]["start"]))

    def test_htmx_get_returns_partial_template(self):
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/timeslot/_timeslot_form.html")

    def test_htmx_valid_post_returns_updated_form(self):
        post_data = _build_timeslot_post_data(self.timeslot, [self.recurrence])
        post_data[f"timeslot-{self.timeslot.pk}-name"] = "Updated Name"

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/timeslot/_timeslot_form.html")
        self.assertEqual(response.context["form"].instance.pk, self.timeslot.pk)

    def test_htmx_invalid_post_returns_partial_template_with_errors(self):
        post_data = _build_timeslot_post_data(self.timeslot, [self.recurrence])
        formset_prefix = f"timerecurrenceform-{self.timeslot.pk}"
        post_data[f"{formset_prefix}-0-start"] = ""

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/timeslot/_timeslot_form.html")
        self.assertTrue(response.context["formset"].errors)


class TestTimeslotCreateView(TimeslotViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("htmx:timeslot-create")

    def test_get_renders_form_with_formset(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("formset", response.context)

    def test_htmx_get_returns_partial_template(self):
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/timeslot/_timeslot_form.html")
        self.assertTrue(response.context["is_create"])

    def test_htmx_valid_post_returns_fresh_form(self):
        post_data = _build_create_post_data(
            name="New Timeslot",
            start="08:00",
            end="17:00",
            days=[1, 2, 3, 4, 5],
        )

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/timeslot/_timeslot_form.html")
        self.assertIsNone(response.context["form"].instance.pk)
        self.assertTrue(response.context["is_create"])

    def test_htmx_invalid_post_returns_partial_template_with_errors(self):
        post_data = _build_create_post_data(
            name="New Timeslot",
            start="",
            end="17:00",
            days=[1, 2, 3],
        )

        response = self.client.post(self.url, data=post_data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "htmx/timeslot/_timeslot_form.html")
        self.assertGreater(response.context["formset"].total_error_count(), 0)


def _build_create_post_data(name, start, end, days):
    """Build POST data for creating a new timeslot."""
    return {
        "name": name,
        "TOTAL_FORMS": "1",
        "INITIAL_FORMS": "0",
        "MIN_NUM_FORMS": "1",
        "MAX_NUM_FORMS": "1000",
        "0-start": start,
        "0-end": end,
        "0-days": [str(d) for d in days],
    }


def _build_timeslot_post_data(timeslot, recurrences, delete_indices=None):
    """Build POST data for updating a timeslot with recurrences."""
    delete_indices = delete_indices or []
    form_prefix = f"timeslot-{timeslot.pk}"
    formset_prefix = f"timerecurrenceform-{timeslot.pk}"

    data = {
        f"{form_prefix}-name": timeslot.name,
        f"{formset_prefix}-TOTAL_FORMS": str(len(recurrences)),
        f"{formset_prefix}-INITIAL_FORMS": str(len(recurrences)),
        f"{formset_prefix}-MIN_NUM_FORMS": "1",
        f"{formset_prefix}-MAX_NUM_FORMS": "1000",
    }

    for i, recurrence in enumerate(recurrences):
        data.update(
            {
                f"{formset_prefix}-{i}-id": str(recurrence.pk),
                f"{formset_prefix}-{i}-timeslot": str(timeslot.pk),
                f"{formset_prefix}-{i}-start": recurrence.start.strftime("%H:%M"),
                f"{formset_prefix}-{i}-end": recurrence.end.strftime("%H:%M"),
                f"{formset_prefix}-{i}-days": [str(d) for d in recurrence.days],
            }
        )
        if i in delete_indices:
            data[f"{formset_prefix}-{i}-DELETE"] = "on"

    return data
