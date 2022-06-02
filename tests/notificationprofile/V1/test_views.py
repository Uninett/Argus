from django.urls import reverse
from django.test import tag

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase

from argus.incident.serializers import IncidentSerializer
from argus.notificationprofile.factories import (
    DestinationConfigFactory,
    FilterFactory,
    NotificationProfileFactory,
    TimeslotFactory,
)
from argus.notificationprofile.models import (
    Media,
    NotificationProfile,
    Filter,
    Timeslot,
)
from argus.util.testing import disconnect_signals, connect_signals

from .. import IncidentAPITestCaseHelper


@tag("API", "integration")
class ViewTests(APITestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()

        incident1_json = IncidentSerializer([self.incident1], many=True).data
        self.incident1_json = JSONRenderer().render(incident1_json)

        self.timeslot1 = TimeslotFactory(user=self.user1, name="Never")
        self.timeslot2 = TimeslotFactory(user=self.user1, name="Never 2: Ever-expanding Void")
        self.filter1 = FilterFactory(
            user=self.user1,
            name="Critical incidents",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=self.timeslot1)
        self.notification_profile1.filters.add(self.filter1)
        self.filter2 = FilterFactory(
            user=self.user1,
            name="Unused filter",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.notification_profile1.destinations.set(self.user1.destinations.all())
        self.media = ["EM", "SM"]
        self.sms_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474700"},
        )

        self.notification_profile1.destinations.set(self.user1.destinations.all())
        self.media = ["EM", "SM"]

    def teardown(self):
        connect_signals()

    def test_incidents_filtered_by_notification_profile_view(self):
        # /api/v1/notificationprofiles/<int:pk>/incidents/
        response = self.user1_rest_client.get(
            reverse("v1:notification-profile:notificationprofile-incidents", args=[self.notification_profile1.pk])
        )
        response.render()
        self.assertEqual(response.content, self.incident1_json)

    def test_notification_profile_can_update_timeslot_without_changing_pk(self):
        # Originally timeslot was the pk of notification profile
        profile1_pk = self.notification_profile1.pk
        profile1_path = reverse("v1:notification-profile:notificationprofile-detail", args=[profile1_pk])

        response = self.user1_rest_client.put(
            profile1_path,
            {
                "timeslot": self.timeslot2.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "media": self.media,
                "phone_number": self.sms_destination.pk,
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], profile1_pk)
        self.assertEqual(NotificationProfile.objects.get(pk=profile1_pk).timeslot.pk, self.timeslot2.pk)

    def test_get_notification_profile_by_pk(self):
        profile_pk = self.notification_profile1.pk
        # /api/v1/notificationprofiles/<int:pk>/
        response = self.user1_rest_client.get(
            reverse("v1:notification-profile:notificationprofile-detail", args=[profile_pk])
        )
        response.render()
        self.assertEqual(response.data["pk"], profile_pk)

    def test_get_notification_profiles(self):
        # /api/v1/notificationprofiles/
        response = self.user1_rest_client.get(reverse("v1:notification-profile:notificationprofile-list"))
        response.render()
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], self.notification_profile1.pk)

    def test_post_new_notification_profile(self):
        # /api/v1/notificationprofiles/
        response = self.user1_rest_client.post(
            reverse("v1:notification-profile:notificationprofile-list"),
            {
                "timeslot": self.timeslot2.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "media": self.media_v1,
                "phone_number": self.sms_destination.pk,
                "active": self.notification_profile1.active,
            },
        )
        response.render()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(NotificationProfile.objects.filter(pk=response.data.get("pk")))

    def test_new_notificaton_profile_has_correct_media(self):
        # /api/v1/notificationprofiles/
        response = self.user1_rest_client.post(
            reverse("v1:notification-profile:notificationprofile-list"),
            {
                "timeslot": self.timeslot2.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "media": self.media_v1,
                "phone_number": self.phone_number,
                "active": self.notification_profile1.active,
            },
        )
        response.render()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["media"], self.media_v1)

    def test_delete_notification_profile(self):
        profile_pk = self.notification_profile1.pk
        # /api/v1/notificationprofiles/<int:pk>/
        response = self.user1_rest_client.delete(
            reverse("v1:notification-profile:notificationprofile-detail", args=[profile_pk])
        )
        response.render()
        self.assertEqual(response.status_code, 204)
        self.assertFalse(NotificationProfile.objects.filter(pk=profile_pk).first())

    def test_get_timeslots(self):
        # /api/v1/notificationprofiles/timeslots/
        response = self.user1_rest_client.get(reverse("v1:notification-profile:timeslot-list"))
        response.render()
        default_timeslot = Timeslot.objects.filter(user=self.user1, name="All the time").first()
        timeslot_pks = set([default_timeslot.pk, self.timeslot1.pk, self.timeslot2.pk])
        response_pks = set([timeslot["pk"] for timeslot in response.data])
        self.assertEqual(timeslot_pks, response_pks)

    def test_create_new_timeslot(self):
        # /api/v1/notificationprofiles/timeslots/
        response = self.user1_rest_client.post(
            reverse("v1:notification-profile:timeslot-list"),
            {
                "name": "test-timeslot",
                "time_recurrences": [{"days": [1, 2, 3], "start": "10:00:00", "end": "20:00:00"}],
            },
        )
        response.render()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Timeslot.objects.filter(user=self.user1, name="test-timeslot").first())

    def test_create_new_timeslot_end_before_start(self):
        # /api/v1/notificationprofiles/timeslots/
        response = self.user1_rest_client.post(
            reverse("v1:notification-profile:timeslot-list"),
            {
                "name": "test-timeslot",
                "time_recurrences": [{"days": [1, 2, 3], "start": "20:00:00", "end": "10:00:00"}],
            },
        )
        response.render()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Timeslot.objects.filter(user=self.user1, name="test-timeslot").first())

    def test_get_timeslot_by_pk(self):
        timeslot_pk = self.timeslot1.pk
        # /api/v1/notificationprofiles/timeslots/<int:pk>/
        response = self.user1_rest_client.get(reverse("v1:notification-profile:timeslot-detail", args=[timeslot_pk]))
        response.render()
        self.assertEqual(response.data["pk"], timeslot_pk)

    def test_update_timeslot_name(self):
        timeslot_pk = self.timeslot1.pk
        new_name = "new-test-name"
        # /api/v1/notificationprofiles/timeslots/<int:pk>/
        response = self.user1_rest_client.put(
            reverse("v1:notification-profile:timeslot-detail", args=[timeslot_pk]),
            {"name": new_name, "time_recurrences": [{"days": [1, 2, 3], "start": "10:00:00", "end": "20:00:00"}]},
        )
        response.render()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Timeslot.objects.filter(pk=timeslot_pk).first().name, new_name)

    def test_update_timeslot_end_to_before_start(self):
        timeslot_pk = self.timeslot1.pk
        # /api/v1/notificationprofiles/timeslots/<int:pk>/
        response = self.user1_rest_client.put(
            reverse("v1:notification-profile:timeslot-detail", args=[timeslot_pk]),
            {
                "name": self.timeslot1.name,
                "time_recurrences": [{"days": [1, 2, 3], "start": "20:00:00", "end": "10:00:00"}],
            },
        )
        response.render()
        self.assertEqual(response.status_code, 400)

    def test_delete_timeslot(self):
        timeslot_pk = self.timeslot1.pk
        # /api/v1/notificationprofiles/timeslots/<int:pk>/
        response = self.user1_rest_client.delete(reverse("v1:notification-profile:timeslot-detail", args=[timeslot_pk]))
        response.render()
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Timeslot.objects.filter(pk=timeslot_pk).first())

    def test_get_filters(self):
        # /api/v1/notificationprofiles/filters/
        response = self.user1_rest_client.get(reverse("v1:notification-profile:filter-list"))
        response.render()
        self.assertTrue(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], self.filter1.pk)

    def test_create_new_filter(self):
        # /api/v1/notificationprofiles/filters/
        response = self.user1_rest_client.post(
            reverse("v1:notification-profile:filter-list"),
            {
                "name": "test-filter",
                "filter_string": f'{{"sourceSystemIds": [{self.source1.pk}], "tags": ["key1=value"]}}',
            },
        )
        response.render()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Filter.objects.filter(user=self.user1, name="test-filter").first())

    def test_get_filter_by_pk(self):
        filter_pk = self.filter1.pk
        # /api/v1/notificationprofiles/filters/<int:pk>/
        response = self.user1_rest_client.get(reverse("v1:notification-profile:filter-detail", args=[filter_pk]))
        response.render()
        self.assertEqual(response.data["pk"], filter_pk)

    def test_update_filter_name(self):
        filter_pk = self.filter1.pk
        new_name = "new-test-name"
        # /api/v1/notificationprofiles/filters/<int:pk>/
        response = self.user1_rest_client.put(
            reverse("v1:notification-profile:filter-detail", args=[filter_pk]),
            {
                "name": new_name,
                "filter_string": f'{{"sourceSystemIds": [{self.source1.pk}], "tags": ["key1=value"]}}',
            },
        )
        response.render()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Filter.objects.filter(pk=filter_pk).first().name, new_name)

    def test_delete_unused_filter_is_deleted(self):
        filter_pk = self.filter2.pk
        # /api/v1/notificationprofiles/filters/<int:pk>/
        response = self.user1_rest_client.delete(reverse("v1:notification-profile:filter-detail", args=[filter_pk]))
        response.render()
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Filter.objects.filter(pk=filter_pk).first())

    def test_delete_used_filter_is_not_deleted(self):
        filter_pk = self.filter1.pk
        # /api/v1/notificationprofiles/filters/<int:pk>/
        response = self.user1_rest_client.delete(reverse("v1:notification-profile:filter-detail", args=[filter_pk]))
        response.render()
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Filter.objects.filter(pk=filter_pk).first())

    def test_get_filterpreview(self):
        # /api/v1/notificationprofiles/filterpreview/
        response = self.user1_rest_client.post(
            reverse("v1:notification-profile:filter-preview"),
            {"sourceSystemIds": [self.source1.pk], "tags": [str(self.tag1)]},
        )
        response.render()
        self.assertTrue(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], self.incident1.pk)
