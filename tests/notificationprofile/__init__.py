from argus.incident.factories import (
    IncidentTagRelationFactory,
    StatelessIncidentFactory,
    SourceSystemTypeFactory,
    SourceSystemFactory,
    SourceUserFactory,
    TagFactory,
)

from ..incident import IncidentBasedAPITestCaseHelper


class IncidentAPITestCaseHelper(IncidentBasedAPITestCaseHelper):
    def init_test_objects(self):
        super().init_test_objects()
        self.source_type2 = SourceSystemTypeFactory(name="type2")
        self.source2_user = SourceUserFactory(username="system_2")
        self.source2 = SourceSystemFactory(name="System 2", type=self.source_type2, user=self.source2_user)

        self.incident1 = StatelessIncidentFactory(source=self.source1)
        self.incident2 = StatelessIncidentFactory(source=self.source2)

        self.tag1 = TagFactory(key="object", value="1")
        self.tag2 = TagFactory(key="object", value="2")
        self.tag3 = TagFactory(key="location", value="Oslo")

        IncidentTagRelationFactory(tag=self.tag1, incident=self.incident1, added_by=self.user1)
        IncidentTagRelationFactory(tag=self.tag3, incident=self.incident1, added_by=self.user1)
        IncidentTagRelationFactory(tag=self.tag2, incident=self.incident2, added_by=self.user1)
        IncidentTagRelationFactory(tag=self.tag3, incident=self.incident2, added_by=self.user1)
