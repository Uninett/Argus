from typing import Union

from django.contrib.auth.models import AbstractUser, Group


class User(AbstractUser):
    @property
    def is_source_system(self):
        return hasattr(self, "source_system")

    @property
    def is_end_user(self):
        return not hasattr(self, "source_system")

    def is_member_of_group(self, group: Union[str, Group]):
        if isinstance(group, str):
            try:
                group = Group.objects.get(name=group)
            except Group.DoesNotExist:
                return None
        return group in self.groups.all()

    def is_used(self):
        # user has created events
        if self.caused_events.exists():
            return True

        # user is a source system that has created incidents
        source = getattr(self, "source_system", None)
        if source and source.incidents.exists():
            return True

        # notification_profiles: manually created but user is safe to
        # delete
        # timeslots: autocreated per person user
        # destinations: autocreated per user with email via social auth

        # user is not considered in use
        return False
