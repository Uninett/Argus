from datetime import timedelta

from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from argus.auth.factories import AdminUserFactory, PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.htmx.plannedmaintenance.views import FILTER_PREVIEW_LIMIT
from argus.incident.factories import StatefulIncidentFactory, SourceSystemFactory
from argus.plannedmaintenance.factories import PlannedMaintenanceFactory
from argus.plannedmaintenance.models import MODIFICATION_WINDOW_PM, PlannedMaintenanceTask
from argus.util.datetime_utils import LOCAL_INFINITY


@tag("integration")
class PlannedMaintenanceListViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()

        now = timezone.now()
        self.future_pm = PlannedMaintenanceFactory(
            start_time=now + timedelta(days=1),
            end_time=LOCAL_INFINITY,
        )
        self.current_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(hours=1),
            end_time=LOCAL_INFINITY,
        )
        self.past_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=1),
        )

    def test_list_view_requires_login(self):
        response = self.client.get(reverse("htmx:plannedmaintenance-list"))
        self.assertEqual(response.status_code, 302)

    def test_list_view_accessible_by_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-list"))
        self.assertEqual(response.status_code, 200)

    def test_list_view_default_tab_is_upcoming(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-list"))
        self.assertEqual(response.context["current_tab"], "upcoming")

    def test_upcoming_tab_shows_current_and_future_tasks(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-list", kwargs={"tab": "upcoming"}))
        object_list = list(response.context["object_list"])
        self.assertIn(self.current_pm, object_list)
        self.assertIn(self.future_pm, object_list)
        self.assertNotIn(self.past_pm, object_list)

    def test_past_tab_shows_past_tasks(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-list", kwargs={"tab": "past"}))
        object_list = list(response.context["object_list"])
        self.assertIn(self.past_pm, object_list)
        self.assertNotIn(self.current_pm, object_list)
        self.assertNotIn(self.future_pm, object_list)

    def test_page_title_is_set(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-list"))
        self.assertEqual(response.context["page_title"], "Planned Maintenance")


@tag("integration")
class PlannedMaintenanceCreateViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()

    def test_create_view_requires_staff(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-create"))
        self.assertEqual(response.status_code, 403)

    def test_create_view_accessible_by_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:plannedmaintenance-create"))
        self.assertEqual(response.status_code, 200)

    def test_create_view_has_initial_start_time(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:plannedmaintenance-create"))
        form = response.context["form"]
        self.assertIn("start_time", form.initial)

    def test_create_view_sets_created_by(self):
        self.client.force_login(self.staff_user)
        test_filter = FilterFactory(user=self.staff_user)
        now = timezone.now()
        response = self.client.post(
            reverse("htmx:plannedmaintenance-create"),
            {
                "start_time": (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                "end_time": (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
                "description": "Test maintenance",
                "filters": [test_filter.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        pm = PlannedMaintenanceTask.objects.get(description="Test maintenance")
        self.assertEqual(pm.created_by, self.staff_user)


@tag("integration")
class PlannedMaintenanceDetailViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.pm = PlannedMaintenanceFactory()

    def test_detail_view_accessible_by_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-detail", kwargs={"pk": self.pm.pk}))
        self.assertEqual(response.status_code, 200)

    def test_detail_view_uses_form_template(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-detail", kwargs={"pk": self.pm.pk}))
        template_names = [t.name for t in response.templates]
        self.assertIn("htmx/plannedmaintenance/plannedmaintenance_form.html", template_names)


@tag("integration")
class PlannedMaintenanceUpdateViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()

        now = timezone.now()
        self.future_pm = PlannedMaintenanceFactory(
            start_time=now + timedelta(days=1),
            end_time=LOCAL_INFINITY,
        )
        self.current_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(days=1),
            end_time=LOCAL_INFINITY,
        )
        self.non_modifiable_pm = PlannedMaintenanceFactory(
            start_time=now - MODIFICATION_WINDOW_PM - timedelta(hours=2),
            end_time=now - MODIFICATION_WINDOW_PM - timedelta(hours=1),
        )

    def test_update_view_requires_staff(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-update", kwargs={"pk": self.future_pm.pk}))
        self.assertEqual(response.status_code, 403)

    def test_update_view_accessible_by_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:plannedmaintenance-update", kwargs={"pk": self.future_pm.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_view_denied_for_non_modifiable_task(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:plannedmaintenance-update", kwargs={"pk": self.non_modifiable_pm.pk}))
        self.assertEqual(response.status_code, 403)

    def test_update_view_future_task_has_start_time_field(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:plannedmaintenance-update", kwargs={"pk": self.future_pm.pk}))
        form = response.context["form"]
        self.assertIn("start_time", form.fields)

    def test_update_view_ongoing_task_does_not_have_start_time_field(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("htmx:plannedmaintenance-update", kwargs={"pk": self.current_pm.pk}))
        form = response.context["form"]
        self.assertNotIn("start_time", form.fields)


@tag("integration")
class PlannedMaintenanceDeleteViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()

        now = timezone.now()
        self.future_pm = PlannedMaintenanceFactory(
            start_time=now + timedelta(days=1),
            end_time=LOCAL_INFINITY,
        )
        self.non_modifiable_pm = PlannedMaintenanceFactory(
            start_time=now - MODIFICATION_WINDOW_PM - timedelta(hours=2),
            end_time=now - MODIFICATION_WINDOW_PM - timedelta(hours=1),
        )

    def test_delete_view_requires_staff(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("htmx:plannedmaintenance-delete", kwargs={"pk": self.future_pm.pk}))
        self.assertEqual(response.status_code, 403)

    def test_delete_view_denied_for_non_modifiable_task(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("htmx:plannedmaintenance-delete", kwargs={"pk": self.non_modifiable_pm.pk}))
        self.assertEqual(response.status_code, 403)

    def test_delete_view_deletes_task(self):
        self.client.force_login(self.staff_user)
        pm_id = self.future_pm.pk
        response = self.client.post(reverse("htmx:plannedmaintenance-delete", kwargs={"pk": pm_id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PlannedMaintenanceTask.objects.filter(pk=pm_id).exists())


@tag("integration")
class PlannedMaintenanceCancelViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.staff_user = AdminUserFactory()

        now = timezone.now()
        self.current_pm = PlannedMaintenanceFactory(
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
        )
        self.non_modifiable_pm = PlannedMaintenanceFactory(
            start_time=now - MODIFICATION_WINDOW_PM - timedelta(hours=2),
            end_time=now - MODIFICATION_WINDOW_PM - timedelta(hours=1),
        )

    def test_cancel_view_requires_staff(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("htmx:plannedmaintenance-cancel", kwargs={"pk": self.current_pm.pk}))
        self.assertEqual(response.status_code, 403)

    def test_cancel_view_denied_for_non_modifiable_task(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("htmx:plannedmaintenance-cancel", kwargs={"pk": self.non_modifiable_pm.pk}))
        self.assertEqual(response.status_code, 403)

    def test_cancel_view_redirects_on_success(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse("htmx:plannedmaintenance-cancel", kwargs={"pk": self.current_pm.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("htmx:plannedmaintenance-list"))


@tag("integration")
class SearchFiltersViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory(username="felaali", first_name="Ferrari", last_name="Testarossa")
        self.other_user = PersonUserFactory(username="lambo", first_name="Lamborghini", last_name="Countach")

        self.user_filter = FilterFactory(user=self.user, name="My Filter")
        self.other_filter = FilterFactory(user=self.other_user, name="Other Filter")

    def test_search_filters_requires_login(self):
        response = self.client.get(reverse("htmx:search-filters"))
        self.assertEqual(response.status_code, 302)

    def test_search_filters_returns_json(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:search-filters"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_search_filters_returns_all_filters_without_query(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:search-filters"))
        data = response.json()
        self.assertEqual(len(data["results"]), 2)

    def test_search_filters_filters_by_name(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:search-filters"), {"q": "My"})
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], self.user_filter.pk)

    def test_search_filters_filters_by_username(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:search-filters"), {"q": self.other_user.username})
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], self.other_filter.pk)

    def test_search_filters_sorts_current_user_filters_first(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:search-filters"))
        data = response.json()
        self.assertEqual(data["results"][0]["id"], self.user_filter.pk)


@tag("integration")
class FilterPreviewViewTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()

    def test_filter_preview_requires_login(self):
        response = self.client.get(reverse("htmx:plannedmaintenance-filter-preview"))
        self.assertEqual(response.status_code, 302)

    def test_filter_preview_without_filters_shows_no_filters(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("htmx:plannedmaintenance-filter-preview"))
        self.assertTrue(response.context["no_filters"])

    def test_filter_preview_with_filters_shows_counts(self):
        self.client.force_login(self.user)
        # Create an open incident
        incident = StatefulIncidentFactory()

        # Create a filter that matches by source
        filter_with_match = FilterFactory(
            user=self.user,
            filter={"sourceSystemIds": [incident.source.pk]},
        )

        response = self.client.get(
            reverse("htmx:plannedmaintenance-filter-preview"),
            {"filters": [filter_with_match.pk]},
        )

        self.assertIn("matching_count", response.context)
        self.assertIn("matching_percent", response.context)
        self.assertIn("total_open", response.context)
        self.assertEqual(response.context["matching_count"], 1)

    def test_filter_preview_with_no_matching_incidents(self):
        self.client.force_login(self.user)
        # Create an open incident
        StatefulIncidentFactory()

        # Create a filter that matches nothing (non-existent source ID)
        filter_no_match = FilterFactory(
            user=self.user,
            filter={"sourceSystemIds": [99999]},
        )

        response = self.client.get(
            reverse("htmx:plannedmaintenance-filter-preview"),
            {"filters": [filter_no_match.pk]},
        )

        self.assertEqual(response.context["matching_count"], 0)

    def test_filter_preview_with_no_open_incidents(self):
        self.client.force_login(self.user)
        # Don't create any incidents - tests division by zero guard
        filter_obj = FilterFactory(user=self.user)

        response = self.client.get(
            reverse("htmx:plannedmaintenance-filter-preview"),
            {"filters": [filter_obj.pk]},
        )

        self.assertEqual(response.context["matching_count"], 0)
        self.assertEqual(response.context["matching_percent"], 0)

    def test_filter_preview_intersects_multiple_filters(self):
        self.client.force_login(self.user)
        # Create two incidents with different sources
        incident1 = StatefulIncidentFactory()
        StatefulIncidentFactory()

        # Create two filters: one matching incident1's source, one matching a non-existent source
        filter1 = FilterFactory(
            user=self.user,
            filter={"sourceSystemIds": [incident1.source.pk]},
        )
        filter2 = FilterFactory(
            user=self.user,
            filter={"sourceSystemIds": [99999]},
        )

        response = self.client.get(
            reverse("htmx:plannedmaintenance-filter-preview"),
            {"filters": [filter1.pk, filter2.pk]},
        )

        # AND logic: no incident matches both filters
        self.assertEqual(response.context["matching_count"], 0)

    def test_filter_preview_limits_incident_list(self):
        self.client.force_login(self.user)
        source = SourceSystemFactory()
        # Create more incidents than the limit
        for _ in range(FILTER_PREVIEW_LIMIT + 1):
            StatefulIncidentFactory(source=source)

        filter_obj = FilterFactory(
            user=self.user,
            filter={"sourceSystemIds": [source.pk]},
        )

        response = self.client.get(
            reverse("htmx:plannedmaintenance-filter-preview"),
            {"filters": [filter_obj.pk]},
        )

        self.assertEqual(response.context["matching_count"], FILTER_PREVIEW_LIMIT + 1)
        self.assertEqual(len(response.context["incident_list"]), FILTER_PREVIEW_LIMIT)
