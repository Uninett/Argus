from rest_framework.test import APIClient

from argus.auth.models import User
from ..models import SourceSystem, SourceSystemType


class IncidentBasedAPITestCaseHelper:
    def init_test_objects(self):
        self.source_type1 = SourceSystemType.objects.create(name="type1")
        self.source1_user = User.objects.create_user(username="system_1")
        self.source1 = SourceSystem.objects.create(name="System 1", type=self.source_type1, user=self.source1_user)

        self.user1 = User.objects.create_user(username="user1", is_staff=True, is_superuser=True)

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        self.source1_rest_client = APIClient()
        self.source1_rest_client.force_authenticate(user=self.source1_user)
