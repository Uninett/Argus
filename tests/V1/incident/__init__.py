from rest_framework.test import APIClient

from argus.auth.factories import SourceUserFactory, AdminUserFactory
from argus.incident.factories import SourceSystemFactory, SourceSystemTypeFactory


class IncidentBasedAPITestCaseHelper:
    def init_test_objects(self):
        self.source_type1 = SourceSystemTypeFactory(name="type1")
        self.source1_user = SourceUserFactory(username="system_1")
        self.source1 = SourceSystemFactory(name="System 1", type=self.source_type1, user=self.source1_user)

        self.user1 = AdminUserFactory(username="user1")

        self.user1_rest_client = APIClient()
        self.user1_rest_client.force_authenticate(user=self.user1)

        self.source1_rest_client = APIClient()
        self.source1_rest_client.force_authenticate(user=self.source1_user)
