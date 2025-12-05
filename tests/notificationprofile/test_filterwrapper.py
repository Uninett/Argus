from datetime import timedelta

from django.test import tag
from django.test import TestCase as DjangoTestCase
from django.utils.timezone import now as tznow

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.incident.factories import SourceSystemFactory
from argus.incident.factories import StatefulIncidentFactory
from argus.notificationprofile.factories import NotificationProfileFactory, TimeRecurrenceFactory
from argus.notificationprofile.filterwrapper import NotificationProfileFilterWrapper
from argus.notificationprofile.models import Timeslot
from argus.util.testing import disconnect_signals, connect_signals


@tag("unittest")
class NotificationProfileFilterWrapperTests(DjangoTestCase):
    def setUp(self):
        disconnect_signals()
        self.source = SourceSystemFactory(name="vfdgtnhj")
        self.incident = StatefulIncidentFactory(start_time=tznow(), source=self.source)
        self.incident.create_first_event()
        self.user = PersonUserFactory()
        timeslot = self.user.timeslots.first()  # all the time-timeslot!
        self.profile = NotificationProfileFactory(user=self.user, timeslot=timeslot, active=True)

    def tearDown(self):
        connect_signals()

    def test_incident_fits_single_filter(self):
        filtr = FilterFactory(user=self.user, filter={"sourceSystemIds": [self.source.id]})
        self.profile.filters.add(filtr)

        npfw = NotificationProfileFilterWrapper(self.profile)
        self.assertTrue(npfw.incident_fits(self.incident))

    def test_incident_fits_fails_on_multiple_conflicting_filters(self):
        filtr = FilterFactory(user=self.user, filter={"sourceSystemIds": [self.source.id]})
        self.profile.filters.add(filtr)
        other_filter = FilterFactory(user=self.user, filter={"sourceSystemIds": [0]})
        self.profile.filters.add(other_filter)

        npfw = NotificationProfileFilterWrapper(self.profile)
        self.assertFalse(npfw.incident_fits(self.incident))

    def test_incident_fits_succeeds_on_multiple_compatible_filters(self):
        filtr = FilterFactory(user=self.user, filter={"sourceSystemIds": [self.source.id]})
        self.profile.filters.add(filtr)
        other_filter = FilterFactory(user=self.user, filter={"maxlevel": self.incident.level})
        self.profile.filters.add(other_filter)

        npfw = NotificationProfileFilterWrapper(self.profile)
        self.assertTrue(npfw.incident_fits(self.incident))

    def test_inactive_profiles_never_fit(self):
        self.profile.active = False
        self.profile.save()

        # we know this fits
        filtr = FilterFactory(user=self.user, filter={"sourceSystemIds": [self.source.id]})
        self.profile.filters.add(filtr)

        npfw = NotificationProfileFilterWrapper(self.profile)
        self.assertFalse(npfw.incident_fits(self.incident))
        self.assertFalse(npfw.event_fits(self.incident.events.first()))
        self.assertFalse(npfw.filter_fits(self.incident.events.first()))

    def test_time_outside_of_timeslot_never_fits(self):
        user = PersonUserFactory()

        # timeslot always before current time
        today = tznow()
        yesterday = today - timedelta(days=1)
        timeslot = Timeslot.objects.create(name="Eternal Yesterday", user=user)
        TimeRecurrenceFactory(
            timeslot=timeslot,
            days=[yesterday.isoweekday()],
        )
        profile = NotificationProfileFactory(user=user, timeslot=timeslot, active=True)

        npfw = NotificationProfileFilterWrapper(profile)
        self.assertFalse(npfw.timeslot_fits(today))
        self.assertFalse(npfw.incident_fits(self.incident))
