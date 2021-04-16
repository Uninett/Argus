from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from ..models import Incident
from ..serializers import IncidentPureDeserializer
from ..views import IncidentViewSet, BooleanStringOAEnum
from .serializers import IncidentSerializerV1


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="acked",
                description="Fetch acked (`true`) or unacked (`false`) incidents.",
                enum=BooleanStringOAEnum,
            ),
            OpenApiParameter(name="cursor", description="The pagination cursor value.", type=str),
            OpenApiParameter(
                name="end_time__gte",
                description="Fetch incidents that ended on or after `END_TIME`",
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="end_time__isnull",
                description='Fetch incidents that have `end_time` set to None (`true`), a datetime or "infinity" (`false`).',
                enum=BooleanStringOAEnum,
            ),
            OpenApiParameter(
                name="end_time__lte",
                description="Fetch incidents that ended on or before `END_TIME`",
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="level__lte",
                description="Fetch incidents with levels less than or equal to `LEVEL`",
                enum=Incident.LEVELS,
            ),
            OpenApiParameter(
                name="open",
                description="Fetch open (`true`) or closed (`false`) incidents.",
                enum=BooleanStringOAEnum,
            ),
            OpenApiParameter(
                name="source__id__in",
                description="Fetch incidents with a source with numeric id `ID1` or `ID2` or..",
            ),
            OpenApiParameter(
                name="source_incident_id",
                description="Fetch incidents with the specific source incident id.",
            ),
            OpenApiParameter(
                name="source__name__in",
                description="Fetch incidents with a source with name ``NAME1`` or ``NAME2`` or..",
            ),
            OpenApiParameter(
                name="source__type__in",
                description="Fetch incidents with a source of a type with numeric id `ID1` or `ID2` or..",
            ),
            OpenApiParameter(
                name="start_time__gte",
                description="Fetch incidents that started on or after `START_TIME`",
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="start_time__lte",
                description="Fetch incidents that started on or before `START_TIME`",
                type=OpenApiTypes.DATETIME,
            ),
            OpenApiParameter(
                name="stateful",
                description="Fetch stateful (`true`) or stateless (`false`) incidents.",
                enum=BooleanStringOAEnum,
            ),
        ]
    )
)
class IncidentViewSetV1(IncidentViewSet):
    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return IncidentPureDeserializer
        return IncidentSerializerV1
