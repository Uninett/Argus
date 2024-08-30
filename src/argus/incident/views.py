import logging
import secrets

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter
from drf_rw_serializers import viewsets as rw_viewsets
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied, MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from argus.auth.models import User
from argus.drf.permissions import IsSuperuserOrReadOnly
from argus.incident.models import Acknowledgement, Event
from argus.incident.ticket.base import (
    TicketClientException,
    TicketCreationException,
    TicketPluginException,
    TicketSettingsException,
)
from argus.incident.ticket.utils import (
    get_autocreate_ticket_plugin,
    serialize_incident_for_ticket_autocreation,
)
from argus.notificationprofile.media import (
    send_notifications_to_users,
    background_send_notification,
)
from argus.filter import get_filter_backend
from argus.util.datetime_utils import INFINITY_REPR
from argus.util.signals import bulk_changed
from argus.util.utils import import_class_from_dotted_path

from .forms import AddSourceSystemForm
from .models import (
    ChangeEvent,
    Event,
    Incident,
    SourceSystem,
    SourceSystemType,
    Tag,
)
from .serializers import (
    UpdateAcknowledgementSerializer,
    EmptySerializer,
    EventSerializer,
    IncidentPureDeserializer,
    IncidentSerializer,
    IncidentTicketUrlSerializer,
    RequestAcknowledgementSerializer,
    RequestBulkAcknowledgementSerializer,
    RequestBulkEventSerializer,
    RequestBulkTicketUrlSerializer,
    ResponseAcknowledgementSerializer,
    ResponseBulkSerializer,
    SourceSystemSerializer,
    SourceSystemTypeSerializer,
    TagSerializer,
    IncidentTagRelation,
)

filter_backend = get_filter_backend()
IncidentFilter = filter_backend.IncidentFilter
SourceLockedIncidentFilter = filter_backend.SourceLockedIncidentFilter
INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS = filter_backend.INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS
SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS = (
    filter_backend.SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS
)

LOG = logging.getLogger(__name__)


def send_changed_incidents(incidents):
    bulk_changed.send(sender=Incident, instances=incidents)


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
        parameters=INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS,
    )
)
class IncidentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """All incidents

    Paged using a cursor
    """

    pagination_class = IncidentPagination
    permission_classes = [IsAuthenticated]
    queryset = Incident.objects.prefetch_default_related()
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    filterset_class = IncidentFilter
    search_fields = ["description", "search_text"]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return IncidentPureDeserializer
        return IncidentSerializer

    def get_queryset(self):
        if self.request.method != "GET":
            return super().get_queryset()
        return (
            Incident.objects.prefetch_default_related().select_related("source").prefetch_related("events__ack").all()
        )

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
                raise ValidationError(f"SourceSystem with pk={source_pk} does not exist.")
        else:
            try:
                source = user.source_system
            except SourceSystem.DoesNotExist:
                raise ValidationError("The requesting user must have a connected source system.")

        # TODO: send notifications to users
        try:
            serializer.save(user=user, source=source)
        except IntegrityError as e:
            # TODO: this should be replaced by more verbose feedback, that also doesn't reference database tables
            raise serializers.ValidationError(e)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        responses={
            204: OpenApiResponse(response=None),
            403: OpenApiResponse(response=None),
            405: OpenApiResponse(response=None),
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an existing incident

        Can only be done if: the setting "INDELIBLE_INCIDENTS" is False.

        Can only be done by:

        * The same source that created the incident
        * Superuser
        """
        if getattr(settings, "INDELIBLE_INCIDENTS", True):
            raise MethodNotAllowed(
                "DELETE", detail="Deletion of incidents is turned off, see setting INDELIBLE_INCIDENTS"
            )
        instance = self.get_object()
        source = getattr(self.request.user, "source_system", None)
        owns_instance = source and source == instance.source
        if self.request.user.is_superuser or owns_instance:
            ack_events = instance.events.filter(type=Event.Type.ACKNOWLEDGE)
            Acknowledgement.objects.filter(event__in=ack_events).delete()
            instance.events.all().delete()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        if not owns_instance:
            raise PermissionDenied(detail="{source} is not originating source, may not delete incident #{instance.id}")
        raise PermissionDenied(detail="Only superusers may delete any incident")

    @extend_schema(request=IncidentTicketUrlSerializer, responses=IncidentTicketUrlSerializer)
    @action(detail=True, methods=["put"])
    def ticket_url(self, request, pk=None):
        """This endpoint manually sets the ticket URL of an incident."""
        incident = self.get_object()
        serializer = IncidentTicketUrlSerializer(data=request.data)
        if serializer.is_valid():
            old_url = incident.ticket_url
            new_url = serializer.data["ticket_url"]
            if old_url != new_url:
                description = ChangeEvent.format_description("ticket_url", old_url, new_url)
                ChangeEvent.objects.create(
                    incident=incident, actor=request.user, timestamp=timezone.now(), description=description
                )
                incident.ticket_url = serializer.data["ticket_url"]
                incident.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    update=extend_schema(
        request=EmptySerializer,
    ),
)
class TicketPluginViewSet(viewsets.ViewSet):
    """This endpoint will automatically create a pre-filled ticket in a ticket
    system that is configured in the settings and return its URL or return the
    URL of an existing linked ticket.
    To change the URL the endpoint /api/v1/incidents/<int:pk>/ticket_url/
    should be used.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = IncidentTicketUrlSerializer
    queryset = Incident.objects.all()

    def update(self, request, incident_pk=None):
        incident = get_object_or_404(self.queryset, pk=incident_pk)

        # never overwrite existing url
        if incident.ticket_url:
            serializer = self.serializer_class(data={"ticket_url": incident.ticket_url})
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket_plugin = get_autocreate_ticket_plugin()
        except TicketSettingsException as e:
            # shouldn't this be a 500 Server Error?
            return Response(data=str(e), status=status.HTTP_400_BAD_REQUEST)

        serialized_incident = serialize_incident_for_ticket_autocreation(incident, request.user)

        try:
            url = ticket_plugin.create_ticket(serialized_incident)
        except TicketSettingsException as e:
            return Response(
                data=str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TicketClientException as e:
            return Response(
                data=str(e),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except TicketCreationException as e:
            return Response(
                data=str(e),
                status=status.HTTP_403_FORBIDDEN,
            )
        except TicketPluginException as e:
            return Response(
                data=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if url:
            incident.change_ticket_url(request.user, url, timezone.now())
            serializer = self.serializer_class(data={"ticket_url": incident.ticket_url})
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            data="No url could be generated. Please check that the ticket plugin provides a function to create tickets.",
            status=status.HTTP_400_BAD_REQUEST,
        )


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
        try:
            key, value = Tag.split(self.kwargs[lookup_url_kwarg])
        except (ValueError, ValidationError) as e:
            # Not a valid tag. Misses the delimiter, or multiple delimiters
            raise ValidationError(str(e))
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


@extend_schema_view(
    list=extend_schema(
        parameters=SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS,
    )
)
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
    create=extend_schema(
        request=RequestAcknowledgementSerializer,
        responses={"201": ResponseAcknowledgementSerializer},
    ),
    update=extend_schema(
        request=UpdateAcknowledgementSerializer,
        responses={"200": ResponseAcknowledgementSerializer},
    ),
    partial_update=extend_schema(
        request=UpdateAcknowledgementSerializer,
        responses={"200": ResponseAcknowledgementSerializer},
    ),
)
class AcknowledgementViewSet(rw_viewsets.ModelViewSet):
    queryset = Incident.objects.none()  # For OpenAPI
    permission_classes = [IsAuthenticated]
    serializer_class = ResponseAcknowledgementSerializer
    read_serializer_class = ResponseAcknowledgementSerializer

    def get_write_serializer_class(self):
        if self.action in ("partial_update", "update"):
            return UpdateAcknowledgementSerializer
        return RequestAcknowledgementSerializer

    def get_incident(self):
        incident_pk = self.kwargs["incident_pk"]
        return get_object_or_404(Incident.objects.all(), pk=incident_pk)

    def get_queryset(self):
        return self.get_incident().acks

    def perform_create(self, serializer: RequestAcknowledgementSerializer):
        user = self.request.user
        incident = self.get_incident()
        serializer.save(incident=incident, actor=user)


class BulkHelper:
    """Methods and attributes that views changing incidents in bulk need"""

    change_key: str

    def bulk_setup(self, incident_ids):
        """Setup needed variables and handle ids not existing in the database

        The setup-part is here because overriding __init__ is error-prone.
        """
        # setup
        changes = {}
        status_codes_seen = set()
        qs = self.queryset.filter(pk__in=incident_ids)
        found_ids = set(qs.values_list("id", flat=True))

        # wash ids
        missing_ids = set(incident_ids) - found_ids
        for missing_id in missing_ids:
            changes[str(missing_id)] = {
                self.change_key: None,
                "status": status.HTTP_400_BAD_REQUEST,
                "errors": {"ids": f"Incident with id {missing_id} could not be found."},
            }
            status_codes_seen.add(status.HTTP_400_BAD_REQUEST)
        return qs, changes, status_codes_seen


@extend_schema_view(
    create=extend_schema(
        request=RequestBulkAcknowledgementSerializer,
        responses=ResponseBulkSerializer,
    )
)
class BulkAcknowledgementViewSet(BulkHelper, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ResponseBulkSerializer
    write_serializer_class = RequestBulkAcknowledgementSerializer
    queryset = Incident.objects.all()
    change_key = "ack"

    def create(self, request):
        serializer = self.write_serializer_class(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        incident_ids = set(serializer.data["ids"])
        actor = request.user
        ack_data = serializer.data["ack"]
        timestamp = ack_data["timestamp"]
        description = ack_data.get("description", "")
        expiration = ack_data.get("expiration", None)

        qs, changes, status_codes_seen = self.bulk_setup(incident_ids)

        acks = qs.create_acks(actor, timestamp, description, expiration)
        # send notifications manually

        event_ids = []
        incidents = []
        for ack in acks:
            event = ack.event
            event_ids.append(event.id)
            incident_id = event.incident_id
            incidents.append(event.incident)
            changes[str(incident_id)] = {
                "ack": ResponseAcknowledgementSerializer(instance=ack).to_representation(instance=ack),
                "status": status.HTTP_201_CREATED,
                "errors": None,
            }
            status_codes_seen.add(status.HTTP_201_CREATED)

        send_changed_incidents(incidents)

        all_bad = status_codes_seen == set((status.HTTP_400_BAD_REQUEST,))
        return Response(
            data={"changes": changes}, status=status.HTTP_400_BAD_REQUEST if all_bad else status.HTTP_201_CREATED
        )


@extend_schema_view(
    create=extend_schema(
        request=RequestBulkEventSerializer,
        responses=ResponseBulkSerializer,
    )
)
class BulkEventViewSet(BulkHelper, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ResponseBulkSerializer
    write_serializer_class = RequestBulkEventSerializer
    queryset = Incident.objects.all()
    change_key = "event"

    def create(self, request):
        serializer = self.write_serializer_class(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        incident_ids = serializer.data["ids"]
        actor = request.user
        event_data = serializer.data["event"]
        timestamp = event_data["timestamp"]
        description = event_data.get("description", "")
        event_type = Event.Type(event_data["type"])

        qs, changes, status_codes_seen = self.bulk_setup(incident_ids)

        if event_type is Event.Type.CLOSE:
            events = qs.close(actor, timestamp, description)
        elif event_type is Event.Type.REOPEN:
            events = qs.reopen(actor, timestamp, description)
        else:
            events = qs.create_events(actor, event_type, timestamp, description)
        # send notifications manually

        incidents = []
        for event in events:
            incident = event.incident
            incidents.append(incident)
            changes[str(incident.id)] = {
                "event": EventSerializer(instance=event).to_representation(instance=event),
                "status": status.HTTP_201_CREATED,
                "errors": None,
            }
            status_codes_seen.add(status.HTTP_201_CREATED)

        send_changed_incidents(incidents)

        all_bad = status_codes_seen == set((status.HTTP_400_BAD_REQUEST,))
        return Response(
            data={"changes": changes}, status=status.HTTP_400_BAD_REQUEST if all_bad else status.HTTP_201_CREATED
        )


@extend_schema_view(
    create=extend_schema(
        request=RequestBulkTicketUrlSerializer,
        responses=ResponseBulkSerializer,
    )
)
class BulkTicketUrlViewSet(BulkHelper, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ResponseBulkSerializer
    write_serializer_class = RequestBulkTicketUrlSerializer
    queryset = Incident.objects.all()
    change_key = "ticket_url"

    def create(self, request):
        serializer = self.write_serializer_class(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        incident_ids = serializer.data["ids"]
        ticket_url = serializer.data["ticket_url"]

        qs, changes, status_codes_seen = self.bulk_setup(incident_ids)

        incidents = qs.update_ticket_url(request.user, ticket_url, timestamp=timezone.now())
        for incident in incidents:
            changes[str(incident.id)] = {
                "ticket_url": ticket_url,
                "status": status.HTTP_201_CREATED,
                "errors": None,
            }
            status_codes_seen.add(status.HTTP_201_CREATED)

        send_changed_incidents(incidents)

        all_bad = status_codes_seen == set((status.HTTP_400_BAD_REQUEST,))
        return Response(
            data={"changes": changes}, status=status.HTTP_400_BAD_REQUEST if all_bad else status.HTTP_201_CREATED
        )
