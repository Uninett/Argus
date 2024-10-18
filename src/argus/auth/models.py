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
