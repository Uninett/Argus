from django.test import tag
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import PersonUserFactory, SourceUserFactory
from argus.filter.factories import FilterFactory
from argus.incident.factories import (
    IncidentTagRelationFactory,
    SourceSystemFactory,
    SourceSystemTypeFactory,
    StatelessIncidentFactory,
    TagFactory,
)
from argus.notificationprofile.factories import (
    DestinationConfigFactory,
    NotificationProfileFactory,
    TimeRecurrenceFactory,
    TimeslotFactory,
)
from argus.notificationprofile.models import (
    DestinationConfig,
    Filter,
    Media,
    NotificationProfile,
    Timeslot,
)
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

        self.timeslot1 = TimeslotFactory(user=self.user1, name="Never")
        self.timeslot2 = TimeslotFactory(user=self.user1, name="Never 2: Ever-expanding Void")
        self.filter1 = FilterFactory(
            user=self.user1,
            name="Critical incidents",
            filter={"sourceSystemIds": [self.source1.pk]},
        )
        self.notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=self.timeslot1)
        self.notification_profile1.filters.add(self.filter1)

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

    def test_should_create_profile_with_valid_values(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "name": "New notification profile",
                "timeslot": self.timeslot1.pk,
                "filters": [self.filter1.pk],
                "destinations": [],
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(NotificationProfile.objects.filter(pk=response.data["pk"]).exists())

    def test_should_create_second_profile_with_empty_name(self):
        # have another profile without name to check that unique name constraint
        # doesn't apply
        NotificationProfileFactory(user=self.user1, name=None)

        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "name": None,
                "timeslot": self.timeslot1.pk,
                "filters": [self.filter1.pk],
                "destinations": [],
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(NotificationProfile.objects.filter(pk=response.data["pk"]).exists())

    def test_should_not_create_profile_with_duplicate_name(self):
        name = "My profile"
        self.notification_profile1.name = name
        self.notification_profile1.save()

        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "name": name,
                "timeslot": self.timeslot1.pk,
                "filters": [self.filter1.pk],
                "destinations": [],
                "active": self.notification_profile1.active,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            NotificationProfile.objects.filter(
                user=self.user1,
                name=name,
            ).count(),
            1,
        )

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

    def test_updating_profile_with_name_of_other_profile_should_fail(self):
        name = "My profile"
        NotificationProfileFactory(user=self.user1, name=name)
        profile1_pk = self.notification_profile1.pk
        profile1_path = f"{self.ENDPOINT}{profile1_pk}/"

        response = self.user1_rest_client.put(
            path=profile1_path,
            data={
                "timeslot": self.timeslot1.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "destinations": [self.synced_email_destination.pk],
                "active": self.notification_profile1.active,
                "name": name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            NotificationProfile.objects.filter(
                user=self.user1,
                name=name,
            ).count(),
            1,
        )

    def test_updating_profile_to_empty_name_should_succeed(self):
        # have another profile without name to check that unique name constraint
        # doesn't apply
        NotificationProfileFactory(user=self.user1, name=None)

        profile1_pk = self.notification_profile1.pk
        profile1_path = f"{self.ENDPOINT}{profile1_pk}/"

        response = self.user1_rest_client.put(
            path=profile1_path,
            data={
                "timeslot": self.timeslot1.pk,
                "filters": [f.pk for f in self.notification_profile1.filters.all()],
                "destinations": [self.synced_email_destination.pk],
                "active": self.notification_profile1.active,
                "name": None,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(NotificationProfile.objects.get(pk=profile1_pk).name, None)

    def test_should_delete_profile(self):
        profile1_pk = self.notification_profile1.pk
        profile1_path = f"{self.ENDPOINT}{profile1_pk}/"
        response = self.user1_rest_client.delete(path=profile1_path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(NotificationProfile.objects.filter(pk=profile1_pk).exists())

    def test_should_not_break_on_trying_to_delete_nonexisting_profile(self):
        non_existent_pk = NotificationProfile.objects.last().id + 1
        non_existent_profile_path = f"{self.ENDPOINT}{non_existent_pk}/"
        response = self.user1_rest_client.delete(path=non_existent_profile_path)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@tag("API", "queryset-filter", "integration")
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
            filter={"sourceSystemIds": [self.source1.pk]},
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
class NotificationFilterIncidentViewTests(APITestCase):
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

        self.tag1 = TagFactory(key="object", value="1")
        self.tag2 = TagFactory(key="object", value="2")

        IncidentTagRelationFactory(tag=self.tag1, incident=self.incident1, added_by=user1)
        IncidentTagRelationFactory(tag=self.tag2, incident=incident2, added_by=user1)

        timeslot1 = TimeslotFactory(user=user1, name="Never")
        filter1 = FilterFactory(
            user=user1,
            name="Critical incidents",
            filter={"sourceSystemIds": [self.source1.pk]},
        )
        self.notification_profile1 = NotificationProfileFactory(user=user1, timeslot=timeslot1)
        self.notification_profile1.filters.add(filter1)

    def teardown(self):
        connect_signals()

    def test_filterpreview_returns_only_incidents_matching_specified_filter(self):
        response = self.user1_rest_client.post(
            "/api/v2/notificationprofiles/filterpreview/",
            {"sourceSystemIds": [self.source1.pk], "tags": [str(self.tag1)]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], self.incident1.pk)

    def test_preview_returns_only_incidents_matching_specified_filter(self):
        response = self.user1_rest_client.post(
            "/api/v2/notificationprofiles/preview/",
            {"sourceSystemIds": [self.source1.pk], "tags": [str(self.tag1)]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], self.incident1.pk)


@tag("API", "integration")
class FilterViewTests(APITestCase):
    ENDPOINT = "/api/v2/notificationprofiles/filters/"

    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        source_type = SourceSystemTypeFactory(name="nav")
        source1_user = SourceUserFactory(username="nav1")
        self.source1 = SourceSystemFactory(name="NAV 1", type=source_type, user=source1_user)

        timeslot1 = TimeslotFactory(user=self.user1, name="Never")
        self.filter1 = FilterFactory(
            user=self.user1,
            name="Critical incidents",
            filter={"sourceSystemIds": [self.source1.pk]},
        )
        self.filter2 = FilterFactory(
            user=self.user1,
            name="Unused filter",
            filter={"sourceSystemIds": [self.source1.pk]},
        )
        notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=timeslot1)
        notification_profile1.filters.add(self.filter1)

    def teardown(self):
        connect_signals()

    def test_list_is_reachable(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_list_has_all_filters(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_filters = self.user1.filters.all()
        self.assertEqual(len(response.data), len(all_filters))
        filter_pks = set([filter.pk for filter in all_filters])
        response_pks = set([filter["pk"] for filter in response.data])
        self.assertEqual(response_pks, filter_pks)

    def test_specific_filter_is_reachable(self):
        filter1_pk = self.filter1.pk
        filter1_path = f"{self.ENDPOINT}{filter1_pk}/"
        response = self.user1_rest_client.get(path=filter1_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_get_specific_filter_should_return_the_filter_we_asked_for(self):
        filter1_pk = self.filter1.pk
        filter1_path = f"{self.ENDPOINT}{filter1_pk}/"
        response = self.user1_rest_client.get(path=filter1_path)
        self.assertEqual(response.data["pk"], filter1_pk)

    def test_should_create_filter_with_valid_values(self):
        filter_name = "test-filter"
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "name": filter_name,
                "filter": {"sourceSystemIds": [self.source1.pk], "tags": ["key1=value"]},
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Filter.objects.filter(pk=response.data["pk"]).exists())

    def test_should_create_filter_with_event_types(self):
        filter_name = "test-filter"
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "name": filter_name,
                "filter": {
                    "event_types": [
                        "STA",
                        "END",
                        "CLO",
                        "REO",
                        "OTH",
                    ]
                },
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Filter.objects.filter(pk=response.data["pk"]).exists())

    def test_should_update_filter_name_with_valid_values(self):
        filter1_pk = self.filter1.pk
        filter1_path = f"{self.ENDPOINT}{filter1_pk}/"
        new_name = "new-test-name"
        response = self.user1_rest_client.put(
            path=filter1_path,
            data={
                "name": new_name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Filter.objects.get(pk=filter1_pk).name, new_name)

    def test_should_delete_unused_filter(self):
        unused_filter_pk = self.filter2.pk
        unused_filter_path = f"{self.ENDPOINT}{unused_filter_pk}/"
        response = self.user1_rest_client.delete(path=unused_filter_path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Filter.objects.filter(pk=unused_filter_pk).exists())

    def test_should_not_delete_used_filter(self):
        filter1_pk = self.filter1.pk
        filter1_path = f"{self.ENDPOINT}{filter1_pk}/"
        response = self.user1_rest_client.delete(path=filter1_path)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Filter.objects.filter(pk=filter1_pk).exists())

    def test_should_not_break_on_trying_to_delete_non_existent_filter(self):
        non_existent_pk = Filter.objects.last().id + 1
        non_existent_filter_path = f"{self.ENDPOINT}{non_existent_pk}/"
        response = self.user1_rest_client.delete(path=non_existent_filter_path)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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

    def test_should_get_specific_medium(self):
        response = self.user1_rest_client.get(path=f"/api/v2/notificationprofiles/media/email/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["slug"], "email")


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

    def test_should_indicate_duplicate_destination_when_it_exists(self):
        DestinationConfigFactory(media_id="sms", settings=self.sms_destination.settings)
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.sms_destination.pk}/duplicate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data["is_duplicate"])

    def test_should_not_indicate_duplicate_destination_when_it_doesnt_exist(self):
        response = self.user1_rest_client.get(path=f"{self.ENDPOINT}{self.sms_destination.pk}/duplicate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertFalse(response.data["is_duplicate"])

    def test_should_not_break_on_trying_to_delete_nonexisting_destination(self):
        non_existent_pk = DestinationConfig.objects.last().id + 1
        non_existent_destination_path = f"{self.ENDPOINT}{non_existent_pk}/"
        response = self.user1_rest_client.delete(path=non_existent_destination_path)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@tag("API", "integration")
class TimeslotViewTests(APITestCase):
    ENDPOINT = "/api/v2/notificationprofiles/timeslots/"

    def setUp(self):
        disconnect_signals()
        self.user1 = PersonUserFactory()

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        source_type = SourceSystemTypeFactory(name="nav")
        source1_user = SourceUserFactory(username="nav1")
        self.source1 = SourceSystemFactory(name="NAV 1", type=source_type, user=source1_user)

        self.timeslot1 = TimeslotFactory(user=self.user1, name="Never")
        filter1 = FilterFactory(
            user=self.user1,
            name="Critical incidents",
            filter={"sourceSystemIds": [self.source1.pk]},
        )
        notification_profile1 = NotificationProfileFactory(user=self.user1, timeslot=self.timeslot1)
        notification_profile1.filters.add(filter1)

    def teardown(self):
        connect_signals()

    def test_list_is_reachable(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_list_has_all_timeslots(self):
        response = self.user1_rest_client.get(path=self.ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_timeslots = self.user1.timeslots.all()
        self.assertEqual(len(response.data), len(all_timeslots))
        timeslot_pks = set([filter.pk for filter in all_timeslots])
        response_pks = set([filter["pk"] for filter in response.data])
        self.assertEqual(response_pks, timeslot_pks)

    def test_specific_timeslot_is_reachable(self):
        timeslot1_pk = self.timeslot1.pk
        timeslot1_path = f"{self.ENDPOINT}{timeslot1_pk}/"
        response = self.user1_rest_client.get(path=timeslot1_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_get_specific_timeslot_should_return_the_timeslot_we_asked_for(self):
        timeslot1_pk = self.timeslot1.pk
        timeslot1_path = f"{self.ENDPOINT}{timeslot1_pk}/"
        response = self.user1_rest_client.get(path=timeslot1_path)
        self.assertEqual(response.data["pk"], timeslot1_pk)

    def test_should_create_timeslot_with_valid_values(self):
        response = self.user1_rest_client.post(
            path=self.ENDPOINT,
            data={
                "name": "test-timeslot",
                "time_recurrences": [{"days": [1, 2, 3], "start": "10:00:00", "end": "20:00:00"}],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Timeslot.objects.filter(pk=response.data["pk"]).exists())

    def test_should_update_timeslot_name_with_valid_values(self):
        timeslot1_pk = self.timeslot1.pk
        timeslot1_path = f"{self.ENDPOINT}{timeslot1_pk}/"
        new_name = "new-test-name"
        response = self.user1_rest_client.put(
            path=timeslot1_path,
            data={
                "name": new_name,
                "time_recurrences": [{"days": [1, 2, 3], "start": "10:00:00", "end": "20:00:00"}],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Timeslot.objects.get(pk=timeslot1_pk).name, new_name)

    def test_should_update_timeslot_with_empty_time_recurrence(self):
        timeslot = TimeslotFactory(user=self.user1, name="Whatever")
        TimeRecurrenceFactory(timeslot=timeslot)
        timeslot_path = f"{self.ENDPOINT}{timeslot.pk}/"
        new_name = "new-test-name"
        response = self.user1_rest_client.put(
            path=timeslot_path,
            data={
                "name": new_name,
                "time_recurrences": [],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        timeslot.refresh_from_db()
        self.assertFalse(timeslot.time_recurrences.all())

    def test_should_update_timeslot_with_no_time_recurrence(self):
        timeslot = self.timeslot1
        TimeRecurrenceFactory(timeslot=timeslot)
        timeslot_path = f"{self.ENDPOINT}{timeslot.pk}/"
        time_recurrences = list(self.timeslot1.time_recurrences.all())
        new_name = "new-test-name"
        response = self.user1_rest_client.patch(
            path=timeslot_path,
            data={
                "name": new_name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Timeslot.objects.get(pk=timeslot.pk).name, new_name)
        self.assertEqual(list(Timeslot.objects.get(pk=timeslot.pk).time_recurrences.all()), time_recurrences)

    def test_should_delete_unused_timeslot(self):
        timeslot2_pk = TimeslotFactory(user=self.user1, name="Never say never").pk
        timeslot2_path = f"{self.ENDPOINT}{timeslot2_pk}/"
        response = self.user1_rest_client.delete(path=timeslot2_path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Timeslot.objects.filter(pk=timeslot2_pk).exists())

    def test_should_delete_used_timeslot_and_connected_profile(self):
        timeslot1_pk = self.timeslot1.pk
        connected_profiles_pks = [profile.pk for profile in self.timeslot1.notification_profiles.all()]
        timeslot1_path = f"{self.ENDPOINT}{timeslot1_pk}/"
        response = self.user1_rest_client.delete(path=timeslot1_path)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Timeslot.objects.filter(pk=timeslot1_pk).exists())
        for profile_pk in connected_profiles_pks:
            self.assertFalse(NotificationProfile.objects.filter(pk=profile_pk).exists())

    def test_should_not_break_on_trying_to_delete_nonexisting_timeslot(self):
        non_existent_pk = Timeslot.objects.last().id + 1
        non_existent_timeslot_path = f"{self.ENDPOINT}{non_existent_pk}/"
        response = self.user1_rest_client.delete(path=non_existent_timeslot_path)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
