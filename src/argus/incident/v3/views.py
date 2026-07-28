import logging
from itertools import chain

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from django_filters import rest_framework as filters

from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view

from argus.filter import get_filter_backend

from argus.incident.factories import add_tags_to_incident, remove_tags_from_incident
from argus.incident.models import (
    Incident,
    Tag,
)
from argus.incident.validators import validate_tagstring
from argus.incident.views import HeartBeatMixin
from argus.incident.v2.views import (
    BaseIncidentViewSet as BaseIncidentViewSetV2,
    SourceSystemViewSet as SourceSystemViewSetV2,
)
from argus.incident.v3.serializers import (
    IncidentPureDeserializer,
    IncidentSerializer,
    SourceSystemSerializer,
    TagListSerializer,
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


class IncidentTagViewSet(
    HeartBeatMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """View or alter an incident's tags directly

    Input: a list of tag strings, or nothing, depending on HTTP verb
    Output: a list of tag strings, or nothing, depending on HTTP verb

    The list is not paginated.
    """

    queryset = Tag.objects.prefetch_related("incident_tag_relations")
    serializer_class = TagListSerializer
    lookup_url_kwarg = "tag"
    lookup_field = lookup_url_kwarg
    # This is not AO3. If we ever have enough tags on an incident to
    # necessitate pagination we have bigger problems!
    pagination_class = None

    def _get_incident(self):
        incident_pk = self.kwargs.get("incident_pk")
        try:
            incident = Incident.objects.get(pk=incident_pk)
        except Incident.DoesNotExist:
            raise ValidationError(f"An incident with pk={incident_pk} does not exist")
        return incident

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly." % (self.__class__.__name__, lookup_url_kwarg)
        )
        tagstring = self.kwargs[lookup_url_kwarg]
        validate_tagstring(tagstring)

        key, value = Tag.split(self.kwargs[lookup_url_kwarg])

        filter_kwargs = {"key": key, "value": value}
        obj = get_object_or_404(queryset, **filter_kwargs)

        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self, *args, **kwargs):
        # This MUST be set here or drf-spectacular croaks with an entirely
        # irrelevant error message:
        #
        # Warning [IncidentViewSet > IncidentFilter]: Exception raised while
        # trying resolve model field for django-filter field "tags". Defaulting
        # to string (Exception: 'tags')
        #
        # Note how it references a different viewset entirely.

        self.incident = self._get_incident()
        return self.queryset.filter(incident_tag_relations__incident=self.incident)

    # actions

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        output = list(chain(*serializer.data))
        return Response(output)

    def perform_create(self, serializer):
        incident = self._get_incident()
        data = serializer.validated_data
        add_tags_to_incident(incident, *data)
        # ChangeEvent!

    def perform_destroy(self, instance):
        remove_tags_from_incident(self.incident, instance.representation)
        # ChangeEvent!
