from django.test import tag
from django.test import TestCase as DjangoTestCase
from django.utils.timezone import now as tznow

from argus.auth.factories import PersonUserFactory
from argus.filter.factories import FilterFactory
from argus.incident.factories import SourceSystemFactory
from argus.incident.factories import StatefulIncidentFactory
from argus.notificationprofile.factories import NotificationProfileFactory
from argus.notificationprofile.filterwrapper import NotificationProfileFilterWrapper


@tag("unittest")
class NotificationProfileFilterWrapperIncidentFitsTagsTests(DjangoTestCase):
    def setUp(self):
        self.source = SourceSystemFactory(name="vfdgtnhj")
        self.incident = StatefulIncidentFactory(start_time=tznow(), source=self.source)
        self.user = PersonUserFactory()
        timeslot = self.user.timeslots.first()  # all the time-timeslot!
        self.profile = NotificationProfileFactory(user=self.user, timeslot=timeslot, active=True)

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
