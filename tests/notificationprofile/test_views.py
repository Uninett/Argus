from django.test import tag
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import PersonUserFactory, SourceUserFactory
from argus.incident.factories import SourceSystemFactory, SourceSystemTypeFactory, StatelessIncidentFactory
from argus.notificationprofile.factories import (
    DestinationConfigFactory,
    FilterFactory,
    NotificationProfileFactory,
    TimeslotFactory,
)
from argus.notificationprofile.models import Media, NotificationProfile
from argus.util.testing import connect_signals, disconnect_signals


@tag("API", "integration")
class NotificationProfileViewTests(APITestCase):
    ENDPOINT = "/api/v2/notificationprofiles/"

    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        source_type = SourceSystemTypeFactory(name="nav")
        source1_user = SourceUserFactory(username="nav1")
        self.source1 = SourceSystemFactory(name="NAV 1", type=source_type, user=source1_user)

        timeslot1 = TimeslotFactory(user=self.user1, name="Never")
        self.timeslot2 = TimeslotFactory(user=self.user1, name="Never 2: Ever-expanding Void")
        filter1 = FilterFactory(
            user=self.user1,
            name="Critical incidents",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=timeslot1)
        self.notification_profile1.filters.add(filter1)

        # Default email destination is automatically created with user
        self.synced_email_destination = self.user1.destinations.get()
        self.notification_profile1.destinations.set([self.synced_email_destination])

    def teardown(self):
        connect_signals()

    def test_list_is_reachable(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_list_has_all_user_profiles(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        all_profile_pks = set(profile.pk for profile in self.user1.notification_profiles.all())
        all_response_pks = set(profile["pk"] for profile in response.data)
        self.assertEqual(all_response_pks, all_profile_pks)

    def test_specific_profile_is_reachable(self):
        profile1_pk = self.notification_profile1.pk
        profile1_path = f"{self.ENDPOINT}{profile1_pk}/"
        response = self.user1_rest_client.get(path=profile1_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_get_specific_profile_should_return_the_profile_we_asked_for(self):
        profile1_pk = self.notification_profile1.pk
        profile1_path = f"{self.ENDPOINT}{profile1_pk}/"
        response = self.user1_rest_client.get(path=profile1_path)
        self.assertEqual(response.data["pk"], profile1_pk)

    def test_updating_timeslot_should_not_change_pk(self):
        # Originally timeslot was the pk of notification profile
        profile1_pk = self.notification_profile1.pk
        profile1_path = f"{self.ENDPOINT}{profile1_pk}/"

        response = self.user1_rest_client.put(
            path=profile1_path,
            data={
                "timeslot": self.timeslot2.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "destinations": [self.synced_email_destination.pk],
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["pk"], profile1_pk)
        self.assertEqual(NotificationProfile.objects.get(pk=profile1_pk).timeslot.pk, self.timeslot2.pk)


@tag("API", "integration")
class NotificationIncidentViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=user1)

        source_type = SourceSystemTypeFactory(name="nav")
        source1_user = SourceUserFactory(username="nav1")
        self.source1 = SourceSystemFactory(name="NAV 1", type=source_type, user=source1_user)

        source_type2 = SourceSystemTypeFactory(name="type2")
        source2_user = SourceUserFactory(username="system_2")
        self.source2 = SourceSystemFactory(name="System 2", type=source_type2, user=source2_user)

        self.incident1 = StatelessIncidentFactory(source=self.source1)
        incident2 = StatelessIncidentFactory(source=self.source2)

        timeslot1 = TimeslotFactory(user=user1, name="Never")
        filter1 = FilterFactory(
            user=user1,
            name="Critical incidents",
            filter_string=f'{{"sourceSystemIds": [{self.source1.pk}]}}',
        )
        self.notification_profile1 = NotificationProfileFactory(user=user1, timeslot=timeslot1)
        self.notification_profile1.filters.add(filter1)

    def teardown(self):
        connect_signals()

    def test_should_get_list_of_all_incidents_matched_by_notification_profile(self):
        response = self.user1_rest_client.get(
            path=f"/api/v2/notificationprofiles/{self.notification_profile1.pk}/incidents/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 1)  # 1, not 2
        self.assertEqual(response.data[0]["pk"], self.incident1.pk)


@tag("API", "integration")
class MediumViewTests(APITestCase):
    def setUp(self):
        disconnect_signals()
        user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=user1)

    def teardown(self):
        connect_signals()

    def test_should_get_all_media(self):
        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(set([medium["slug"] for medium in response.data]), set(["sms", "email"]))


@tag("API", "integration")
class DestinationViewTests(APITestCase):
    ENDPOINT = "/api/v2/notificationprofiles/destinations/"

    def setUp(self):
        disconnect_signals()
        user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=user1)

        # Default email destination is automatically created with user
        self.synced_email_destination = user1.destinations.get()
        self.non_synced_email_destination = DestinationConfigFactory(
            user=user1,
            media=Media.objects.get(slug="email"),
            settings={"email_address": "test@example.com", "synced": False},
        )
        self.sms_destination = DestinationConfigFactory(
            user=user1,
            media=Media.objects.get(slug="sms"),
            settings={"phone_number": "+4747474747"},
        )

    def teardown(self):
        connect_signals()

    def test_should_get_list_of_all_destinations(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 3, response.data)
        response_settings = [destination["settings"] for destination in response.data]
        self.assertTrue(self.synced_email_destination.settings in response_settings)
        self.assertTrue(self.non_synced_email_destination.settings in response_settings)
        self.assertTrue(self.sms_destination.settings in response_settings)

    def test_should_get_specific_destination(self):
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.synced_email_destination.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["settings"], self.synced_email_destination.settings)
