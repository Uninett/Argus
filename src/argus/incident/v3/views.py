import logging

from django.contrib.auth import get_user_model

from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from drf_spectacular.utils import extend_schema, extend_schema_view

from argus.filter import get_filter_backend

from argus.incident.models import (
    Incident,
)

# from argus.incident.views import HeartBeatMixin
from argus.incident.v2.views import (
    BaseIncidentViewSet as BaseIncidentViewSetV2,
    SourceSystemViewSet as SourceSystemViewSetV2,
)
from argus.incident.v3.serializers import (
    IncidentPureDeserializer,
    IncidentSerializer,
    SourceSystemSerializer,
)

filter_backend = get_filter_backend()
IncidentFilter = filter_backend.IncidentFilter
SourceLockedIncidentFilter = filter_backend.SourceLockedIncidentFilter
INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS = filter_backend.INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS
SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS = (
    filter_backend.SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS
)
User = get_user_model()


LOG = logging.getLogger(__name__)


class SourceSystemViewSet(SourceSystemViewSetV2):
    serializer_class = SourceSystemSerializer


class BaseIncidentViewSet(BaseIncidentViewSetV2):
    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return IncidentPureDeserializer
        return IncidentSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS,
    )
)
class IncidentViewSet(BaseIncidentViewSet):
    """All incidents

    Paged using a cursor
    """

    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    filterset_class = IncidentFilter

    def get_queryset(self):
        if self.request.method != "GET":
            return super().get_queryset()
        return (
            Incident.objects.prefetch_default_related().select_related("source").prefetch_related("events__ack").all()
        )


@extend_schema_view(
    list=extend_schema(
        parameters=SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS,
    )
)
class SourceLockedIncidentViewSet(BaseIncidentViewSet):
    """All incidents added by the currently logged in user

    Paged using a cursor"""

    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = SourceLockedIncidentFilter

    def get_queryset(self):
        return Incident.objects.filter(source__user=self.request.user).prefetch_default_related()
