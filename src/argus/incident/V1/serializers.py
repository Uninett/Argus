from ..models import Incident
from ..serializers import IncidentSerializer


class IncidentSerializerV1(IncidentSerializer):
    class Meta:
        model = Incident
        fields = [
            "pk",
            "start_time",
            "end_time",
            "source",
            "source_incident_id",
            "details_url",
            "description",
            "level",
            "ticket_url",
            "tags",
        ]
        read_only_fields = ["source"]
        extra_kwargs = {"level": {"required": False}}
