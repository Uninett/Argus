from django.test import tag

from rest_framework import status
from rest_framework.test import APITestCase

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
from argus.incident.factories import StatelessIncidentFactory
from argus.util.testing import disconnect_signals, connect_signals

from .. import IncidentAPITestCaseHelper


@tag("API", "integration")
class ViewTests(APITestCase, IncidentAPITestCaseHelper):
    def setUp(self):
        disconnect_signals()
        super().init_test_objects()

        self.timeslot1 = TimeslotFactory(user=self.user1, name="Never")
        self.timeslot2 = TimeslotFactory(user=self.user1, name="Never 2: Ever-expanding Void")
        self.filter1 = FilterFactory(
            user=self.user1,
            name="Critical incidents",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=self.timeslot1)
        self.notification_profile1.filters.add(self.filter1)
        self.sms_destination = DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474700"},
        )

        self.notification_profile1.destinations.set(self.user1.destinations.all())
        self.media = ["EM", "SM"]

    def teardown(self):
        connect_signals()

    def test_can_get_all_incidents_of_notification_profile(self):
        StatelessIncidentFactory(source=self.source1)
        StatelessIncidentFactory(source=self.source1)
        response = self.user1_rest_client.get(
            f"/api/v1/notificationprofiles/{self.notification_profile1.pk}/incidents/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_incidents = self.notification_profile1.filtered_incidents
        self.assertEqual(len(response.data), len(all_incidents))
        all_incident_pks = set([incident.pk for incident in all_incidents])
        all_response_pks = set([incident["pk"] for incident in response.data])
        self.assertEqual(all_response_pks, all_incident_pks)

    def test_can_update_timeslot_for_notification_profile_with_valid_values(self):
        profile1_pk = self.notification_profile1.pk
        profile1_path = f"/api/v1/notificationprofiles/{profile1_pk}/"
        response = self.user1_rest_client.put(
            profile1_path,
            {
                "timeslot": self.timeslot2.pk,
                "filters": [self.filter1.pk],
                "media": self.media,
                "phone_number": self.sms_destination.pk,
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], profile1_pk)
        self.assertEqual(NotificationProfile.objects.get(pk=profile1_pk).timeslot.pk, self.timeslot2.pk)

    def test_can_get_specific_notification_profile(self):
        profile_pk = self.notification_profile1.pk
        response = self.user1_rest_client.get(f"/api/v1/notificationprofiles/{profile_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], profile_pk)

    def test_can_get_all_notification_profiles(self):
        NotificationProfileFactory(user=self.user1)
        NotificationProfileFactory(user=self.user1)
        response = self.user1_rest_client.get("/api/v1/notificationprofiles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_notifprofiles = self.user1.notification_profiles.all()
        self.assertEqual(len(response.data), len(all_notifprofiles))
        notifprofile_pks = set([notifprofile.pk for notifprofile in all_notifprofiles])
        response_pks = set([notifprofile["pk"] for notifprofile in response.data])
        self.assertEqual(response_pks, notifprofile_pks)

    def test_can_create_notification_profile_with_valid_values(self):
        response = self.user1_rest_client.post(
            "/api/v1/notificationprofiles/",
            {
                "timeslot": self.timeslot2.pk,
                "filters": [self.filter1.pk],
                "media": self.media,
                "phone_number": self.sms_destination.pk,
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(NotificationProfile.objects.filter(pk=response.data["pk"]).exists())

    def test_new_notificaton_profiles_have_correct_media(self):
        response = self.user1_rest_client.post(
            "/api/v1/notificationprofiles/",
            {
                "timeslot": self.timeslot2.pk,
                "filters": [self.filter1.pk],
                "media": self.media,
                "phone_number": self.sms_destination.pk,
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["media"], self.media)

    def test_can_delete_notification_profile(self):
        profile_pk = self.notification_profile1.pk
        response = self.user1_rest_client.delete(f"/api/v1/notificationprofiles/{profile_pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(NotificationProfile.objects.filter(pk=profile_pk).exists())

    def test_can_get_all_timeslots(self):
        TimeslotFactory(user=self.user1)
        TimeslotFactory(user=self.user1)
        response = self.user1_rest_client.get("/api/v1/notificationprofiles/timeslots/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_timeslots = self.user1.timeslots.all()
        self.assertEqual(len(response.data), len(all_timeslots))
        timeslot_pks = set([timeslot.pk for timeslot in all_timeslots])
        response_pks = set([timeslot["pk"] for timeslot in response.data])
        self.assertEqual(response_pks, timeslot_pks)

    def test_can_create_timeslot_with_valid_values(self):
        response = self.user1_rest_client.post(
            "/api/v1/notificationprofiles/timeslots/",
            {
                "name": "test-timeslot",
                "time_recurrences": [{"days": [1, 2, 3], "start": "10:00:00", "end": "20:00:00"}],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Timeslot.objects.filter(pk=response.data["pk"]).exists())

    def test_cannot_create_timeslot_with_end_time_before_start_time(self):
        response = self.user1_rest_client.post(
            "/api/v1/notificationprofiles/timeslots/",
            {
                "name": "test-timeslot",
                "time_recurrences": [{"days": [1, 2, 3], "start": "20:00:00", "end": "10:00:00"}],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Timeslot.objects.filter(user=self.user1, name="test-timeslot").exists())

    def test_can_get_specific_timeslot(self):
        timeslot_pk = self.timeslot1.pk
        response = self.user1_rest_client.get(f"/api/v1/notificationprofiles/timeslots/{timeslot_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], timeslot_pk)

    def test_can_update_timeslot_name_with_valid_values(self):
        timeslot_pk = self.timeslot1.pk
        new_name = "new-test-name"
        response = self.user1_rest_client.put(
            f"/api/v1/notificationprofiles/timeslots/{timeslot_pk}/",
            {"name": new_name, "time_recurrences": [{"days": [1, 2, 3], "start": "10:00:00", "end": "20:00:00"}]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Timeslot.objects.get(pk=timeslot_pk).name, new_name)

    def test_cannot_update_timeslot_end_time_to_before_start_time(self):
        timeslot_pk = self.timeslot1.pk
        new_recurrences = [{"days": [1, 2, 3], "start": "20:00:00", "end": "10:00:00"}]
        response = self.user1_rest_client.put(
            f"/api/v1/notificationprofiles/timeslots/{timeslot_pk}/",
            {
                "name": self.timeslot1.name,
                "time_recurrences": new_recurrences,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(Timeslot.objects.get(id=timeslot_pk).time_recurrences, new_recurrences)

    def test_can_delete_timeslot(self):
        timeslot_pk = self.timeslot1.pk
        response = self.user1_rest_client.delete(f"/api/v1/notificationprofiles/timeslots/{timeslot_pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Timeslot.objects.filter(pk=timeslot_pk).exists())

    def test_can_get_all_filters(self):
        FilterFactory(user=self.user1)
        FilterFactory(user=self.user1)
        response = self.user1_rest_client.get("/api/v1/notificationprofiles/filters/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_filters = self.user1.filters.all()
        self.assertEqual(len(response.data), len(all_filters))
        filter_pks = set([filter.pk for filter in all_filters])
        response_pks = set([filter["pk"] for filter in response.data])
        self.assertEqual(response_pks, filter_pks)

    def test_can_create_filter_with_valid_values(self):
        filter_name = "test-filter"
        response = self.user1_rest_client.post(
            "/api/v1/notificationprofiles/filters/",
            {
                "name": filter_name,
                "filter_string": f'{{"sourceSystemIds": [{self.source1.pk}], "tags": ["key1=value"]}}',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Filter.objects.filter(pk=response.data["pk"]).exists())

    def test_can_get_specific_filter(self):
        filter_pk = self.filter1.pk
        response = self.user1_rest_client.get(f"/api/v1/notificationprofiles/filters/{filter_pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pk"], filter_pk)

    def test_can_update_filter_name_with_valid_values(self):
        filter_pk = self.filter1.pk
        new_name = "new-test-name"
        response = self.user1_rest_client.put(
            f"/api/v1/notificationprofiles/filters/{filter_pk}/",
            {
                "name": new_name,
                "filter_string": f'{{"sourceSystemIds": [{self.source1.pk}], "tags": ["key1=value"]}}',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Filter.objects.get(pk=filter_pk).name, new_name)

    def test_can_delete_unused_filter(self):
        filter = FilterFactory(
            user=self.user1,
            name="Unused filter",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        response = self.user1_rest_client.delete(f"/api/v1/notificationprofiles/filters/{filter.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Filter.objects.filter(pk=filter.pk).exists())

    def test_cannot_delete_used_filter(self):
        filter_pk = self.filter1.pk
        response = self.user1_rest_client.delete(f"/api/v1/notificationprofiles/filters/{filter_pk}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Filter.objects.filter(pk=filter_pk).exists())

    def test_filterpreview_returns_only_incidents_matching_specified_filter(self):
        response = self.user1_rest_client.post(
            "/api/v1/notificationprofiles/filterpreview/",
            {"sourceSystemIds": [self.source1.pk], "tags": [str(self.tag1)]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], self.incident1.pk)

    def test_preview_returns_only_incidents_matching_specified_filter(self):
        response = self.user1_rest_client.post(
            "/api/v1/notificationprofiles/preview/",
            {"sourceSystemIds": [self.source1.pk], "tags": [str(self.tag1)]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], self.incident1.pk)
