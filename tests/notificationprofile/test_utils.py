from django.test import TestCase

from argus.auth.factories import AdminUserFactory
from argus.filter.factories import FilterFactory
from argus.notificationprofile.models import Filter
from argus.notificationprofile.utils import annotate_public_filters_with_usernames


class AnnotatePublicFiltersWithUsernameTests(TestCase):
    def setUp(self):
        self.user1 = AdminUserFactory()
        self.user2 = AdminUserFactory()

    def test_adds_username_for_public_filters(self):
        public_filter = FilterFactory(user=self.user2, public=True)

        qs = annotate_public_filters_with_usernames(qs=Filter.objects.filter(id=public_filter.id), user=self.user1)

        label = qs.get(id=public_filter.id).label
        assert public_filter.name in label
        assert self.user2.username in label

    def test_does_not_add_user_for_own_filters(self):
        own_filter = FilterFactory(user=self.user1)

        qs = annotate_public_filters_with_usernames(qs=Filter.objects.filter(id=own_filter.id), user=self.user1)

        label = qs.get(id=own_filter.id).label
        assert own_filter.name in label
        assert self.user1.username not in label
