import secrets

from django.db import IntegrityError
from django.urls import reverse

from django_filters import rest_framework as filters
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from argus.auth.models import User
from argus.drf.permissions import IsOwnerOrReadOnly, IsSuperuserOrReadOnly
from argus.util.datetime_utils import INFINITY_REPR
from .forms import AddSourceSystemForm
from .filters import IncidentFilter, SourceLockedIncidentFilter
from .models import (
    Event,
    Incident,
    SourceSystem,
    SourceSystemType,
)
from .serializers import (
    AcknowledgementSerializer,
    EventSerializer,
    IncidentPureDeserializer,
    IncidentSerializer,
    IncidentTicketUrlSerializer,
    SourceSystemSerializer,
    SourceSystemTypeSerializer,
)


class IncidentPagination(CursorPagination):
    ordering = "-start_time"
    page_size_query_param = "page_size"


class SourceSystemTypeList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SourceSystemTypeSerializer
    queryset = SourceSystemType.objects.all()


class SourceSystemList(generics.ListCreateAPIView):
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


class SourceSystemDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = SourceSystem.objects.all()
    serializer_class = SourceSystemSerializer


class IncidentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = IncidentPagination
    permission_classes = [IsAuthenticated]
    queryset = Incident.objects.prefetch_default_related().prefetch_related("source")
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = IncidentFilter

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return IncidentPureDeserializer
        return IncidentSerializer

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

    @action(detail=True, methods=["put"])
    def ticket_url(self, request, pk=None):
        incident = self.get_object()
        serializer = IncidentTicketUrlSerializer(data=request.data)
        if serializer.is_valid():
            incident.ticket_url = serializer.data["ticket_url"]
            incident.save()
            # TODO: make argus stateless incident about the url being saved? event?
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SourceLockedIncidentViewSet(IncidentViewSet):
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = SourceLockedIncidentFilter

    def get_queryset(self):
        return Incident.objects.filter(source__user=self.request.user).prefetch_default_related()


class OpenUnAckedIncidentList(generics.ListAPIView):
    serializer_class = IncidentSerializer

    def get_queryset(self):
        return Incident.objects.open().not_acked().prefetch_default_related()


class OpenIncidentList(generics.ListAPIView):
    serializer_class = IncidentSerializer

    def get_queryset(self):
        return Incident.objects.open().prefetch_default_related()


class EventViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
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
            if event_type == Event.Type.INCIDENT_START:
                validate_incident_has_no_relation_to_event_type()
            elif event_type in {Event.Type.INCIDENT_END, Event.Type.CLOSE, Event.Type.REOPEN}:
                self._raise_type_validation_error("Cannot change the state of a stateless incident.")

        if event_type == Event.Type.ACKNOWLEDGE:
            acks_endpoint = reverse("incident:incident-acks", args=[incident.pk])
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


class AcknowledgementViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    serializer_class = AcknowledgementSerializer

    def get_queryset(self):
        incident_pk = self.kwargs["incident_pk"]
        incident = get_object_or_404(Incident.objects.all(), pk=incident_pk)
        return incident.acks

    def perform_create(self, serializer: AcknowledgementSerializer):
        user = self.request.user
        if user.is_source_system:
            EventViewSet._raise_type_validation_error("A source system cannot post acknowledgements.")

        incident = Incident.objects.get(pk=self.kwargs["incident_pk"])
        serializer.save(incident=incident, actor=user)


@api_view(["GET"])
def get_all_meta_data_view(request):
    source_systems = SourceSystemSerializer(SourceSystem.objects.select_related("type"), many=True)
    data = {
        "sourceSystems": source_systems.data,
    }
    return Response(data)
