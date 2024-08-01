from django.test import TestCase, override_settings

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.incident.factories import EventFactory
from argus.incident.models import create_fake_incident, get_or_create_default_instances, Event
from argus.notificationprofile import factories
from argus.notificationprofile.media import find_destinations_for_event
from argus.notificationprofile.media import find_destinations_for_many_events
from argus.notificationprofile.media import get_notification_media
from argus.notificationprofile.media.email import modelinstance_to_dict
from argus.notificationprofile.models import Media
from argus.util.testing import disconnect_signals, connect_signals


class SerializeModelTest(TestCase):
    def test_modelinstance_to_dict_should_not_change_modelinstance(self):
        instance = factories.TimeslotFactory()
        attributes1 = vars(instance)
        modelinstance_to_dict(instance)
        attributes2 = vars(instance)
        self.assertEqual(attributes1, attributes2)


class FindDestinationsTest(TestCase):
    def setUp(self):
        disconnect_signals()

        self.user1 = PersonUserFactory()
        self.user1_destination = self.user1.destinations.get()  # default email
        self.extra_destination1 = factories.DestinationConfigFactory(
            user=self.user1,
            media=Media.objects.get(slug="email"),
            settings={"email": "a@b.ca", "synced": False},
        )

        self.user2 = PersonUserFactory()
        self.user2_destination = self.user2.destinations.get()  # default email
        self.extra_destination2 = factories.DestinationConfigFactory(
            user=self.user2,
            media=Media.objects.get(slug="email"),
            settings={"email": "b@c.de", "synced": False},
        )

        # Create a filter that matches your test incident
        (_, _, argus_source) = get_or_create_default_instances()
        filter_dict1 = {"sourceSystemIds": [argus_source.id]}
        filter1 = FilterFactory(
            user=self.user1,
            filter=filter_dict1,
        )
        filter_dict2 = {"tags": ["foo=bar"]}
        filter2 = FilterFactory(
            user=self.user2,
            filter=filter_dict2,
        )

        # Make a timeslot
        self.timeslot = factories.TimeslotFactory(user=self.user1)
        factories.MaximalTimeRecurrenceFactory(timeslot=self.timeslot)

        # Create two notification profiles that match this filter,
        # with different destinations
        self.np1 = factories.NotificationProfileFactory(user=self.user1, timeslot=self.timeslot, active=True)
        self.np1.filters.add(filter1)
        self.np1.destinations.add(self.user1_destination)

        self.np2 = factories.NotificationProfileFactory(user=self.user2, timeslot=self.timeslot, active=True)
        self.np2.filters.add(filter2)
        self.np2.destinations.add(self.user2_destination)
        self.np2.destinations.add(self.extra_destination2)

    def tearDown(self):
        connect_signals()

    def test_find_destinations_for_event(self):
        incident = create_fake_incident()
        event = incident.events.get(type=Event.Type.INCIDENT_START)
        destinations = find_destinations_for_event(event)
        self.assertEqual(len(destinations), 1)
        self.assertIn(self.user1_destination, destinations)
        self.assertNotIn(self.extra_destination1, destinations)
        self.assertNotIn(self.extra_destination2, destinations)

    def test_find_destinations_for_ack_event_without_acknowledgement(self):
        ack_profile = factories.NotificationProfileFactory(
            user=PersonUserFactory(),
            timeslot=self.timeslot,
            active=True,
        )
        ack_filter = FilterFactory(
            user=ack_profile.user,
            filter={"acked": True},
        )
        ack_profile.filters.add(ack_filter)
        ack_destination = ack_profile.user.destinations.get()  # default email
        ack_profile.destinations.add(ack_destination)

        event = EventFactory(type=Event.Type.ACKNOWLEDGE)
        destinations = find_destinations_for_event(event)
        self.assertIn(ack_destination, destinations)

    def test_find_destinations_by_filtering_by_event_types(self):
        ack_event_type_profile = factories.NotificationProfileFactory(
            user=PersonUserFactory(),
            timeslot=self.timeslot,
            active=True,
        )
        ack_event_type_filter = FilterFactory(
            user=ack_event_type_profile.user,
            filter={"event_types": [Event.Type.ACKNOWLEDGE]},
        )
        ack_event_type_profile.filters.add(ack_event_type_filter)
        ack_destination = ack_event_type_profile.user.destinations.get()  # default email
        ack_event_type_profile.destinations.add(ack_destination)

        event = EventFactory(type=Event.Type.ACKNOWLEDGE)
        destinations = find_destinations_for_event(event)
        self.assertIn(ack_destination, destinations)

    @override_settings(ARGUS_FALLBACK_FILTER={"event_types": ["ACK"]})
    def test_find_destinations_by_filtering_by_event_types_using_fallback_filter(self):
        ack_event_type_profile = factories.NotificationProfileFactory(
            user=PersonUserFactory(),
            timeslot=self.timeslot,
            active=True,
        )
        ack_event_type_filter = FilterFactory(
            user=ack_event_type_profile.user,
            filter={},
        )
        ack_event_type_profile.filters.add(ack_event_type_filter)
        ack_destination = ack_event_type_profile.user.destinations.get()  # default email
        ack_event_type_profile.destinations.add(ack_destination)

        event = EventFactory(type=Event.Type.ACKNOWLEDGE)
        destinations = find_destinations_for_event(event)
        self.assertIn(ack_destination, destinations)

    def test_find_destinations_for_many_events(self):
        incident1 = create_fake_incident()
        event1 = incident1.events.get(type=Event.Type.INCIDENT_START)
        incident1.set_closed(self.user1)
        event2 = incident1.events.get(type=Event.Type.CLOSE)
        incident2 = create_fake_incident(tags=["foo=bar"])
        event3 = incident2.events.get(type=Event.Type.INCIDENT_START)

        destinations = find_destinations_for_many_events((event1, event2, event3))
        self.assertEqual(len(destinations), 3)

        self.assertIn(event1, destinations)
        self.assertIn(self.user1_destination, destinations[event1])
        self.assertNotIn(self.user2_destination, destinations[event1])
        self.assertNotIn(self.extra_destination1, destinations[event1])
        self.assertNotIn(self.extra_destination2, destinations[event1])

        self.assertIn(event2, destinations)
        self.assertIn(self.user1_destination, destinations[event2])
        self.assertNotIn(self.user2_destination, destinations[event2])
        self.assertNotIn(self.extra_destination1, destinations[event2])
        self.assertNotIn(self.extra_destination2, destinations[event2])

        self.assertIn(event3, destinations)
        self.assertIn(self.user1_destination, destinations[event3])
        self.assertIn(self.user2_destination, destinations[event3])
        self.assertNotIn(self.extra_destination1, destinations[event3])
        self.assertIn(self.extra_destination2, destinations[event3])


class GetNotificationMediaTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.installed_media = Media.objects.all()
        self.not_installed_medium = factories.MediaFactory(slug="missing", name="Missing medium", installed=True)

        self.user = PersonUserFactory()

    def tearDown(self):
        connect_signals()

    def test_get_notification_media_will_set_installed_to_false_for_medium_of_destination(self):
        destination = factories.DestinationConfigFactory(user=self.user, media=self.not_installed_medium, settings={})
        get_notification_media(destinations=[destination])

        self.not_installed_medium.refresh_from_db()
        self.assertFalse(self.not_installed_medium.installed)

    def test_get_notification_media_will_not_set_installed_to_false_for_destinations_with_other_media(self):
        get_notification_media(destinations=list(self.user.destinations.all()))

        self.not_installed_medium.refresh_from_db()
        self.assertTrue(self.not_installed_medium.installed)
