from django.utils import timezone

from argus.auth.models import User
from argus.incident.models import (
    Incident,
    IncidentTagRelation,
    SourceSystem,
    SourceSystemType,
    Tag,
)
from argus.util.utils import duplicate

from ..incident import IncidentBasedAPITestCaseHelper


class IncidentAPITestCaseHelper(IncidentBasedAPITestCaseHelper):
    def init_test_objects(self):
        super().init_test_objects()

        self.source_type2 = SourceSystemType.objects.create(name="type2")
        self.source2 = SourceSystem.objects.create(
            name="System 2",
            type=self.source_type2,
            user=User.objects.create(username="system_2"),
        )

        self.incident1 = Incident.objects.create(
            start_time=timezone.now(),
            source=self.source1,
            source_incident_id="123",
        )
        self.incident2 = duplicate(self.incident1, source=self.source2)

        self.tag1 = Tag.objects.create_from_tag("object=1")
        self.tag2 = Tag.objects.create_from_tag("object=2")
        self.tag3 = Tag.objects.create_from_tag("location=Oslo")

        IncidentTagRelation.objects.create(tag=self.tag1, incident=self.incident1, added_by=self.user1)
        IncidentTagRelation.objects.create(tag=self.tag3, incident=self.incident1, added_by=self.user1)
        IncidentTagRelation.objects.create(tag=self.tag2, incident=self.incident2, added_by=self.user1)
        IncidentTagRelation.objects.create(tag=self.tag3, incident=self.incident2, added_by=self.user1)
