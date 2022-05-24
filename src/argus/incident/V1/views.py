from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response

from ..filters import SourceLockedIncidentFilter
from ..models import Incident, SourceSystem
from ..serializers import IncidentPureDeserializer, SourceSystemSerializer

from ..views import IncidentViewSet, BooleanStringOAEnum
from .serializers import IncidentSerializerV1, MetadataSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="acked",
                description="Fetch acked (`true`) or unacked (`false`) incidents.",
                enum=BooleanStringOAEnum,
            ),
            OpenApiParameter(
                name="duration__gte",
                description="Fetch incidents with a duration longer of equal to `DURATION` minutes",
                type=int,
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

    # DEPRECATED: This view will be removed in V2
    @extend_schema(
        responses=MetadataSerializer,
        description=("Metadata used by incidents.\n\nDeprecated, use the individual endpoints instead"),
        deprecated=True,
    )
    @action(detail=False, methods=["get"])
    def metadata(self, request, **_):
        source_systems = SourceSystemSerializer(SourceSystem.objects.select_related("type"), many=True)
        data = {
            "sourceSystems": source_systems.data,
        }
        return Response(data)


class SourceLockedIncidentViewSetV1(IncidentViewSetV1):
    """All incidents added by the currently logged in user

    Paged using a cursor"""

    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = SourceLockedIncidentFilter

    def get_queryset(self):
        return Incident.objects.filter(source__user=self.request.user).prefetch_default_related()


# DEPRECATED: The following views will be removed in V2


@extend_schema_view(get=extend_schema(deprecated=True))
class OpenUnAckedIncidentListV1(generics.ListAPIView):
    """All incidents that are open and unacked

    open: stateful, end_time is "infinity"
    unacked: no acknowledgements are currently in play

    Deprecated: This endpoint will be removed in API version 2.
    Use query parameters ``open=true&acked=false`` with the other Incident list
    endpoints instead.
    """

    serializer_class = IncidentSerializerV1

    def get_queryset(self):
        return Incident.objects.open().not_acked().prefetch_default_related()


@extend_schema_view(get=extend_schema(deprecated=True))
class OpenIncidentListV1(generics.ListAPIView):
    """All incidents that are open

    open: stateful, end_time is "infinity"

    Deprecated: This endpoint will be removed in API version 2.
    Use query parameter ``open=true`` with the other Incident list endpoints
    instead.
    """

    serializer_class = IncidentSerializerV1

    def get_queryset(self):
        return Incident.objects.open().prefetch_default_related()
