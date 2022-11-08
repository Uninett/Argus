import secrets

from django.db import IntegrityError

from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from argus.auth.models import User
from argus.drf.permissions import IsSuperuserOrReadOnly
from argus.util.datetime_utils import INFINITY_REPR

from .forms import AddSourceSystemForm
from .filters import IncidentFilter, SourceLockedIncidentFilter
from .models import (
    Acknowledgement,
    Event,
    Incident,
    SourceSystem,
    SourceSystemType,
    Tag,
)
from .serializers import (
    UpdateAcknowledgementSerializer,
    AcknowledgementSerializer,
    EventSerializer,
    IncidentPureDeserializer,
    IncidentSerializer,
    IncidentTicketUrlSerializer,
    RequestBulkAcknowledgementSerializer,
    ResponseBulkSerializer,
    SourceSystemSerializer,
    SourceSystemTypeSerializer,
    TagSerializer,
    IncidentTagRelation,
)


# Used in OpenApiParameter
BooleanStringOAEnum = ("true", "false")


class IncidentPagination(CursorPagination):
    ordering = "-start_time"
    page_size_query_param = "page_size"


class EventPagination(CursorPagination):
    ordering = "-timestamp"
    page_size_query_param = "page_size"


class SourceSystemTypeViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    serializer_class = SourceSystemTypeSerializer
    queryset = SourceSystemType.objects.all()


class SourceSystemViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsSuperuserOrReadOnly]
    queryset = SourceSystem.objects.all()
    serializer_class = SourceSystemSerializer

    def create(self, request, *args, **kwargs):
        # Reuse the logic in the form that's used on the admin page
        form = AddSourceSystemForm(request.data)
        if not form.is_valid():
            # If the form is invalid because the username is unavailable:
            if User.objects.filter(username=form.data["username"]).exists():
                self._set_available_username(form)
            else:
                raise serializers.ValidationError(form.errors)

        source_system = form.save()
        serializer = SourceSystemSerializer(source_system)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @staticmethod
    def _set_available_username(form: AddSourceSystemForm):
        random_suffix = secrets.token_hex(3).upper()  # 16.8 million distinct values
        username = f"{form.data['username']}_{random_suffix}"
        form.data["username"] = username
        form.full_clean()  # re-checks for errors
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)


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
                name="level__lte", description="Fetch incidents with levels in `LEVEL`", enum=Incident.LEVELS
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
class IncidentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """All incidents

    Paged using a cursor
    """

    pagination_class = IncidentPagination
    permission_classes = [IsAuthenticated]
    queryset = Incident.objects.prefetch_default_related().prefetch_related("source")
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    filterset_class = IncidentFilter
    search_fields = ["description", "search_text"]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return IncidentPureDeserializer
        return IncidentSerializer

    def list(self, request, *args, **kwargs):
        if "count" in request.query_params:
            count = self.filter_queryset(self.get_queryset()).count()
            response_dict = {"count": count, "params": request.query_params}
            return Response(response_dict)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user

        if "source" in serializer.initial_data:
            if not user.is_superuser:
                raise serializers.ValidationError(
                    "You must be a superuser to be allowed to specify the 'source' field."
                )

            source_pk = serializer.initial_data["source"]
            try:
                source = SourceSystem.objects.get(pk=source_pk)
            except SourceSystem.DoesNotExist:
                raise serializers.ValidationError(f"SourceSystem with pk={source_pk} does not exist.")
        else:
            try:
                source = user.source_system
            except SourceSystem.DoesNotExist:
                raise serializers.ValidationError("The requesting user must have a connected source system.")

        # TODO: send notifications to users
        try:
            serializer.save(user=user, source=source)
        except IntegrityError as e:
            # TODO: this should be replaced by more verbose feedback, that also doesn't reference database tables
            raise serializers.ValidationError(e)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(request=IncidentTicketUrlSerializer, responses=IncidentTicketUrlSerializer)
    @action(detail=True, methods=["put"])
    def ticket_url(self, request, pk=None):
        incident = self.get_object()
        serializer = IncidentTicketUrlSerializer(data=request.data)
        if serializer.is_valid():
            incident.ticket_url = serializer.data["ticket_url"]
            incident.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncidentTagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Tag.objects.prefetch_related("incident_tag_relations")
    serializer_class = TagSerializer
    lookup_url_kwarg = "tag"
    lookup_field = lookup_url_kwarg

    def _get_incident(self):
        incident_pk = self.kwargs.get("incident_pk")
        try:
            incident = Incident.objects.get(pk=incident_pk)
        except Incident.DoesNotExist:
            raise NotFound("An incident with this id does not exist")
        return incident

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly." % (self.__class__.__name__, lookup_url_kwarg)
        )
        try:
            key, value = Tag.split(self.kwargs[lookup_url_kwarg])
        except (ValueError, ValidationError) as e:
            # Not a valid tag. Misses the delimiter, or multiple delimiters
            raise NotFound(str(e))
        filter_kwargs = {"key": key, "value": value}
        obj = get_object_or_404(queryset, **filter_kwargs)

        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self, *args, **kwargs):
        incident = self._get_incident()
        return self.queryset.filter(incident_tag_relations__incident=incident)

    def perform_create(self, serializer):
        data = serializer.validated_data
        tag, _ = Tag.objects.get_or_create(**data)
        incident = self._get_incident()
        IncidentTagRelation.objects.get_or_create(incident=incident, tag=tag, defaults={"added_by": self.request.user})

    def perform_destroy(self, instance):
        incident = self._get_incident()
        # Delete the connection between tag and incident
        itrs = IncidentTagRelation.objects.filter(incident=incident, tag=instance)
        if itrs.exists():
            itrs.delete()
            # If the tag is now unused, delete it
            if not IncidentTagRelation.objects.filter(tag=instance).exists():
                instance.delete()


class SourceLockedIncidentViewSet(IncidentViewSet):
    """All incidents added by the currently logged in user

    Paged using a cursor"""

    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = SourceLockedIncidentFilter

    def get_queryset(self):
        return Incident.objects.filter(source__user=self.request.user).prefetch_default_related()


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(name="cursor", description="The pagination cursor value.", type=str),
        ]
    )
)
class AllEventsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pagination_class = EventPagination
    queryset = Event.objects.none()
    permission_classes = [IsAuthenticated]
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.all()


class EventViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Incident.objects.none()  # For OpenAPI
    permission_classes = [IsAuthenticated]
    serializer_class = EventSerializer

    def get_queryset(self):
        incident_pk = self.kwargs["incident_pk"]
        incident = get_object_or_404(Incident.objects.all(), pk=incident_pk)
        return incident.events.all()

    def perform_create(self, serializer: EventSerializer):
        user = self.request.user
        incident = Incident.objects.get(pk=self.kwargs["incident_pk"])

        event_type = serializer.validated_data["type"]
        self.validate_event_type_for_user(event_type, user)
        try:
            self.validate_event_type_for_incident(event_type, incident)
        except serializers.ValidationError as e:
            # Allow any event from source systems (as long as the user is allowed to post the event type),
            # even if the posted type is invalid for the incident - like if an `INCIDENT_END` event
            # is sent after the incident has been manually closed
            if not user.is_source_system:
                raise e
        else:
            # Only update incident if everything is valid; otherwise, just record the event
            self.update_incident(serializer.validated_data, incident)

        serializer.save(incident=incident, actor=user)

    def validate_event_type_for_user(self, event_type: str, user: User):
        if user.is_source_system:
            if event_type not in Event.ALLOWED_TYPES_FOR_SOURCE_SYSTEMS:
                self._raise_type_validation_error(f"A source system cannot post events of type '{event_type}'.")
        else:
            if event_type not in Event.ALLOWED_TYPES_FOR_END_USERS:
                self._raise_type_validation_error(f"An end user cannot post events of type '{event_type}'.")

    def validate_event_type_for_incident(self, event_type: str, incident: Incident):
        def validate_incident_has_no_relation_to_event_type():
            if incident.events.filter(type=event_type).exists():
                self._raise_type_validation_error(f"The incident already has a related event of type '{event_type}'.")

        if incident.stateful:
            if event_type in {Event.Type.INCIDENT_START, Event.Type.INCIDENT_END}:
                validate_incident_has_no_relation_to_event_type()
            if event_type in {Event.Type.INCIDENT_END, Event.Type.CLOSE} and not incident.open:
                self._raise_type_validation_error("The incident is already closed.")
            elif event_type == Event.Type.REOPEN and incident.open:
                self._raise_type_validation_error("The incident is already open.")
        else:
            if event_type == Event.Type.STATELESS:
                validate_incident_has_no_relation_to_event_type()
            elif event_type == Event.Type.INCIDENT_START:
                self._raise_type_validation_error("Stateless incident cannot have an INCIDENT_START event.")
            elif event_type in {Event.Type.INCIDENT_END, Event.Type.CLOSE, Event.Type.REOPEN}:
                self._raise_type_validation_error("Cannot change the state of a stateless incident.")

        if event_type == Event.Type.ACKNOWLEDGE:
            acks_endpoint = reverse("incident:incident-acks", args=[incident.pk], request=self.request)
            self._raise_type_validation_error(
                f"Acknowledgements of this incidents should be posted through {acks_endpoint}."
            )

    def update_incident(self, validated_data: dict, incident: Incident):
        timestamp = validated_data["timestamp"]
        event_type = validated_data["type"]
        if event_type in {Event.Type.INCIDENT_END, Event.Type.CLOSE}:
            incident.end_time = timestamp
            incident.save()
        elif event_type == Event.Type.REOPEN:
            incident.end_time = INFINITY_REPR
            incident.save()

    @staticmethod
    def _raise_type_validation_error(message: str):
        raise serializers.ValidationError({"type": message})


@extend_schema_view(
    update=extend_schema(
        request=UpdateAcknowledgementSerializer,
        responses={"200": AcknowledgementSerializer},
    ),
    partial_update=extend_schema(
        request=UpdateAcknowledgementSerializer,
        responses={"200": AcknowledgementSerializer},
    ),
)
class AcknowledgementViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Incident.objects.none()  # For OpenAPI
    permission_classes = [IsAuthenticated]
    serializer_class = AcknowledgementSerializer

    def get_serializer_class(self):
        if self.action in ("partial_update", "update"):
            return UpdateAcknowledgementSerializer
        return self.serializer_class

    def get_incident(self):
        incident_pk = self.kwargs["incident_pk"]
        return get_object_or_404(Incident.objects.all(), pk=incident_pk)

    def get_queryset(self):
        return self.get_incident().acks

    def perform_create(self, serializer: AcknowledgementSerializer):
        user = self.request.user
        incident = self.get_incident()
        serializer.save(incident=incident, actor=user)


@extend_schema_view(
    create=extend_schema(
        request=RequestBulkAcknowledgementSerializer,
        responses=ResponseBulkSerializer,
    )
)
class BulkAcknowledgementViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ResponseBulkSerializer
    write_serializer_class = RequestBulkAcknowledgementSerializer
    queryset = Incident.objects.all()

    def create(self, request):
        serializer = self.write_serializer_class(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        incident_ids = serializer.data["ids"]
        ack_data = serializer.data["ack"]
        actor = request.user

        incidents = {i.id: i for i in self.queryset.filter(pk__in=incident_ids)}
        changes = {}
        status_codes_seen = set()

        for incident_id in incident_ids:
            incident = incidents.get(incident_id)

            if not incident:
                changes[str(incident_id)] = {
                    "ack": None,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "errors": {"ids": f"Incident with id {incident_id} could not be found."},
                }
                status_codes_seen.add(status.HTTP_400_BAD_REQUEST)
                continue

            event = Event.objects.create(
                incident=incident,
                actor=actor,
                timestamp=ack_data["event"]["timestamp"],
                type=Event.Type.ACKNOWLEDGE,
                description=ack_data["event"]["description"],
            )
            ack = Acknowledgement.objects.create(event=event, expiration=ack_data["expiration"])
            changes[str(incident_id)] = {
                "ack": AcknowledgementSerializer(instance=ack).to_representation(instance=ack),
                "status": status.HTTP_201_CREATED,
                "errors": None,
            }
            status_codes_seen.add(status.HTTP_201_CREATED)

        all_bad = status_codes_seen == set((status.HTTP_400_BAD_REQUEST,))

        return Response(
            data={"changes": changes}, status=status.HTTP_400_BAD_REQUEST if all_bad else status.HTTP_201_CREATED
        )
