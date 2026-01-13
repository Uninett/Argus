from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import TimeslotFactory, TimeRecurrenceFactory


class TestTimeslotUpdateView(TestCase):
    def test_get_renders_form_with_formset(self):
        user = PersonUserFactory()
        timeslot = TimeslotFactory(user=user)
        self.client.force_login(user=user)

        response = self.client.get(reverse("htmx:timeslot-update", kwargs={"pk": timeslot.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertIn("formset", response.context)

    def test_deleting_all_recurrences_shows_warning(self):
        user = PersonUserFactory()
        timeslot = TimeslotFactory(user=user)
        recurrence = TimeRecurrenceFactory(timeslot=timeslot)
        self.client.force_login(user=user)

        post_data = _build_timeslot_post_data(timeslot, [recurrence], delete_indices=[0])

        response = self.client.post(
            reverse("htmx:timeslot-update", kwargs={"pk": timeslot.pk}),
            data=post_data,
        )

        self.assertRedirects(response, reverse("htmx:timeslot-list"), fetch_redirect_response=False)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, "warning")
        self.assertIn("no time recurrences", str(messages[0]))

    def test_invalid_formset_preserves_errors(self):
        user = PersonUserFactory()
        timeslot = TimeslotFactory(user=user)
        recurrence = TimeRecurrenceFactory(timeslot=timeslot)
        self.client.force_login(user=user)

        # Submit with missing required field (empty start time)
        post_data = _build_timeslot_post_data(timeslot, [recurrence])
        formset_prefix = f"timerecurrenceform-{timeslot.pk}"
        post_data[f"{formset_prefix}-0-start"] = ""

        response = self.client.post(
            reverse("htmx:timeslot-update", kwargs={"pk": timeslot.pk}),
            data=post_data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("formset", response.context)
        self.assertTrue(response.context["formset"].errors)


class TestTimeslotCreateView(TestCase):
    def test_get_renders_form_with_formset(self):
        user = PersonUserFactory()
        self.client.force_login(user=user)

        response = self.client.get(reverse("htmx:timeslot-create"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("formset", response.context)

    def test_invalid_formset_preserves_errors(self):
        user = PersonUserFactory()
        self.client.force_login(user=user)

        # Submit with missing required fields
        post_data = {
            "name": "Test Timeslot",
            "time_recurrences-TOTAL_FORMS": "1",
            "time_recurrences-INITIAL_FORMS": "0",
            "time_recurrences-MIN_NUM_FORMS": "1",
            "time_recurrences-MAX_NUM_FORMS": "1000",
            "time_recurrences-0-start": "",
            "time_recurrences-0-end": "",
            "time_recurrences-0-days": [],
        }

        response = self.client.post(reverse("htmx:timeslot-create"), data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("formset", response.context)
        self.assertTrue(response.context["formset"].errors)


def _build_timeslot_post_data(timeslot, recurrences, delete_indices=None):
    """Build POST data for timeslot form with recurrences."""
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
