from django.test import TestCase
import json

from argus.auth.factories import PersonUserFactory
from argus.incident.models import create_fake_incident, get_or_create_default_instances
from argus.notificationprofile import factories
from argus.notificationprofile.media import find_destinations_for_event
from argus.notificationprofile.media.email import modelinstance_to_dict
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
        user = PersonUserFactory()
        self.user = user
        timeslot1 = factories.TimeslotFactory(user=user)
        factories.MaximalTimeRecurrenceFactory(timeslot=timeslot1)
        timeslot2 = factories.TimeslotFactory(user=user)
        factories.MinimalTimeRecurrenceFactory(timeslot=timeslot2)

        # Create a filter that matches your test incident
        (_, _, argus_source) = get_or_create_default_instances()
        filter_dict = {"sourceSystemIds": [argus_source.id], "tags": []}
        filter_string = json.dumps(filter_dict)
        filter = factories.FilterFactory(user=user, filter_string=filter_string)

        # Get user related destinations
        destinations = user.destinations.all()

        # Create two notification profiles that match this filter,
        # but attached to different timeslots
        self.np1 = factories.NotificationProfileFactory(user=user, timeslot=timeslot1, active=True)
        self.np1.filters.add(filter)
        self.np1.destinations.set(destinations)
        self.np2 = factories.NotificationProfileFactory(user=user, timeslot=timeslot2, active=True)
        self.np2.filters.add(filter)
        self.np2.destinations.set(destinations)

    def tearDown(self):
        connect_signals()

    def test_find_destinations_for_event(self):
        incident = create_fake_incident()
        event = incident.events.get(type="STA")
        destinations = find_destinations_for_event(event)
        for destination in self.user.destinations.all():
            self.assertIn(destination, destinations)

