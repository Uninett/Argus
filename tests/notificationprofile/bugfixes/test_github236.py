from django.core import mail
from django.test import TestCase
import json

from argus.auth.factories import PersonUserFactory
from argus.incident.models import create_fake_incident, get_or_create_default_instances
from argus.notificationprofile.factories import (
    TimeslotFactory,
    NotificationProfileFactory,
    FilterFactory,
    MaximalTimeRecurrenceFactory,
    MinimalTimeRecurrenceFactory,
)
from argus.notificationprofile.media import send_notifications_to_users
from argus.notificationprofile.models import Timeslot, NotificationProfile, Filter
from argus.util.testing import disconnect_signals, connect_signals


"""See:

https://github.com/Uninett/Argus/issues/236
"""


class SendingNotificationTest(TestCase):
    def setUp(self):
        disconnect_signals()

        # Create two separate timeslots
        user = PersonUserFactory()
        timeslot1 = TimeslotFactory(user=user)
        MaximalTimeRecurrenceFactory(timeslot=timeslot1)
        timeslot2 = TimeslotFactory(user=user)
        MinimalTimeRecurrenceFactory(timeslot=timeslot2)

        # Create a filter that matches your test incident
        (_, _, argus_source) = get_or_create_default_instances()
        filter_dict = {"sourceSystemIds": [argus_source.id], "tags": []}
        filter_string = json.dumps(filter_dict)
        filter = FilterFactory(user=user, filter_string=filter_string)

        # Create two notification profiles that match this filter, but attached to each their timeslot
        self.np1 = NotificationProfileFactory(user=user, timeslot=timeslot1, active=True)
        self.np1.filters.add(filter)
        self.np2 = NotificationProfileFactory(user=user, timeslot=timeslot2, active=True)
        self.np2.filters.add(filter)

    def tearDown(self):
        connect_signals()

    def test_sending_event_to_multiple_profiles_of_the_same_user_should_not_raise_exception(self):
        LOG_PREFIX = "INFO:argus.notificationprofile.media:"
        # Send a test event
        self.incident = create_fake_incident()
        event = self.incident.events.get(type="STA")
        with self.settings(SEND_NOTIFICATIONS=True):
            try:
                send_notifications_to_users(event)
            except AttributeError:
                self.fail("send_notifications_to_users() should not raise an AttributeError")
            self.assertTrue(bool(mail.outbox), "Mail should have been sent")
