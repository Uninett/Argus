from django.test import TestCase
import json

from argus.auth.factories import PersonUserFactory
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

        # Create two separate timeslots
        self.user = PersonUserFactory()
        timeslot1 = factories.TimeslotFactory(user=self.user)
        factories.MaximalTimeRecurrenceFactory(timeslot=timeslot1)
        timeslot2 = factories.TimeslotFactory(user=self.user)
        factories.MinimalTimeRecurrenceFactory(timeslot=timeslot2)

        # Create a filter that matches your test incident
        (_, _, argus_source) = get_or_create_default_instances()
        filter_dict = {"sourceSystemIds": [argus_source.id], "tags": []}
        filter_string = json.dumps(filter_dict)
        filter = factories.FilterFactory(user=self.user, filter_string=filter_string)

        # Get user related destinations
        # if user.email_address is set then at least one
        self.destinations = self.user.destinations.all()

        # Create two notification profiles that match this filter,
        # but attached to different timeslots
        self.np1 = factories.NotificationProfileFactory(user=self.user, timeslot=timeslot1, active=True)
        self.np1.filters.add(filter)
        self.np1.destinations.set(self.destinations)
        self.np2 = factories.NotificationProfileFactory(user=self.user, timeslot=timeslot2, active=True)
        self.np2.filters.add(filter)
        self.np2.destinations.set(self.destinations)

    def tearDown(self):
        connect_signals()

    def test_find_destinations_for_event(self):
        incident = create_fake_incident()
        event = incident.events.get(type=Event.Type.INCIDENT_START)
        destinations = find_destinations_for_event(event)
        self.assertEqual(len(destinations), 1, 'No destinations found')
        for destination in self.destinations:
            self.assertIn(destination, destinations)

    def test_test_find_destinations_for_many_events(self):
        incident = create_fake_incident()
        event1 = incident.events.get(type=Event.Type.INCIDENT_START)
        incident.set_closed(self.user)
        event2 = incident.events.get(type=Event.Type.CLOSE)
        destinations = find_destinations_for_many_events((event1, event2))
        self.assertEqual(len(destinations), 1, 'No destinations found')
        for destination in self.destinations:
            self.assertIn(destination, destinations)

class GetNotificationMediaTests(TestCase):
    def setUp(self):
        disconnect_signals()

        self.installed_media = Media.objects.all()
        self.not_installed_medium = Media.objects.create(slug="missing", name="Missing medium", installed=True)

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
