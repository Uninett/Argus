import json

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from drf_rw_serializers import viewsets as rw_viewsets

from argus.drf.permissions import IsOwner
from argus.filter import get_filter_backend
from argus.incident.serializers import IncidentSerializer
from argus.notificationprofile.media import api_safely_get_medium_object
from argus.notificationprofile.media.base import NotificationMedium
from .models import DestinationConfig, Filter, Media, NotificationProfile, Timeslot
from .serializers import (
    DuplicateDestinationSerializer,
    JSONSchemaSerializer,
    MediaSerializer,
    ResponseDestinationConfigSerializer,
    RequestDestinationConfigSerializer,
    ResponseNotificationProfileSerializer,
    RequestNotificationProfileSerializer,
    TimeslotSerializer,
)


filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter
FilterSerializer = filter_backend.FilterSerializer
FilterBlobSerializer = filter_backend.FilterBlobSerializer


@extend_schema_view(
    create=extend_schema(
        request=RequestNotificationProfileSerializer,
        responses={201: ResponseNotificationProfileSerializer},
    ),
    update=extend_schema(
        request=RequestNotificationProfileSerializer,
    ),
    partial_update=extend_schema(
        request=RequestNotificationProfileSerializer,
    ),
)
class NotificationProfileViewSet(rw_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ResponseNotificationProfileSerializer
    read_serializer_class = ResponseNotificationProfileSerializer
    write_serializer_class = RequestNotificationProfileSerializer
    queryset = NotificationProfile.objects.none()

    def get_queryset(self):
        return self.request.user.notification_profiles.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        responses={200: IncidentSerializer(many=True)},
    )
    @action(methods=["get"], detail=True)
    def incidents(self, request, pk, *args, **kwargs):
        try:
            notification_profile = request.user.notification_profiles.get(pk=pk)
        except NotificationProfile.DoesNotExist:
            raise ValidationError(f"Notification profile with pk={pk} does not exist.")
        serializer = IncidentSerializer(
            QuerySetFilter.incidents_by_notificationprofile(
                incident_queryset=None,
                notificationprofile=notification_profile,
            ),
            many=True,
        )
        return Response(serializer.data)

    @extend_schema(
        request=FilterBlobSerializer,
        responses=IncidentSerializer(many=True),
    )
    @action(methods=["post"], detail=False)
    def preview(self, request, **_):
        """
        POST a filter, get a list of filtered incidents back

        Format:
        {
            "sourceSystemIds": [1, ..],
            "tags": ["some=tag", ..],
            "open": true,
            "acked": false,
            "stateful": true,
            "maxlevel": 3
        }

        Minimal format:
        {}

        Will eventually take over for the filterpreview endpoint
        """
        filter_dict = request.data
        serializer = FilterBlobSerializer(data=filter_dict)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        serializer = IncidentSerializer(QuerySetFilter.filtered_incidents(serializer.data), many=True)
        return Response(serializer.data)


class SchemaView(DetailView):
    template_name = "schemawrapper.html"
    model = Media

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        medium = api_safely_get_medium_object(self.object.slug)
        kwargs["schema_info"] = medium.MEDIA_JSON_SCHEMA
        return kwargs


class MediaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MediaSerializer
    queryset = Media.objects.none()
    http_method_names = ["get", "head"]

    def get_queryset(self):
        return Media.objects.all()

    @extend_schema(responses={"200": JSONSchemaSerializer})
    @action(methods=["get"], detail=True)
    def json_schema(self, request, pk, *args, **kwargs):
        try:
            medium = api_safely_get_medium_object(pk)
            schema = medium.MEDIA_JSON_SCHEMA
            schema["$id"] = reverse(
                "json-schema",
                kwargs={"slug": pk},
                request=request,
            )
        except KeyError:
            raise ValidationError(f"Medium with pk={pk} does not exist.")
        serializer = JSONSchemaSerializer({"json_schema": schema})
        return Response(serializer.data)


@extend_schema_view(
    create=extend_schema(
        request=RequestDestinationConfigSerializer,
        responses={201: ResponseDestinationConfigSerializer},
    ),
    update=extend_schema(
        request=RequestDestinationConfigSerializer,
    ),
    partial_update=extend_schema(
        request=RequestDestinationConfigSerializer,
    ),
)
class DestinationConfigViewSet(rw_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ResponseDestinationConfigSerializer
    read_serializer_class = ResponseDestinationConfigSerializer
    write_serializer_class = RequestDestinationConfigSerializer
    queryset = DestinationConfig.objects.none()
    http_method_names = ["get", "head", "post", "patch", "delete"]

    def get_queryset(self):
        return self.request.user.destinations.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        destination = get_object_or_404(self.get_queryset(), pk=pk)

        try:
            medium = api_safely_get_medium_object(destination.media.slug)
            medium.raise_if_not_deletable(destination)
        except NotificationMedium.NotDeletableError as e:
            raise ValidationError(str(e))
        else:
            return super().destroy(destination)

    def _is_destination_duplicate(self, destination):
        other_destinations = DestinationConfig.objects.filter(media=destination.media).filter(
            ~Q(user_id=destination.user.id)
        )
        medium = api_safely_get_medium_object(destination.media_id)
        destination_in_use = medium.has_duplicate(other_destinations, destination.settings)
        return destination_in_use

    @extend_schema(
        responses={200: DuplicateDestinationSerializer()},
    )
    @action(methods=["get"], detail=True)
    def duplicate(self, request, pk, *args, **kwargs):
        try:
            destination = request.user.destinations.get(pk=pk)
        except DestinationConfig.DoesNotExist:
            raise ValidationError(f"Destination with pk={pk} does not exist.")
        is_duplicate = self._is_destination_duplicate(destination=destination)
        serializer = DuplicateDestinationSerializer({"is_duplicate": is_duplicate})
        return Response(serializer.data)


class TimeslotViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeslotSerializer
    queryset = Timeslot.objects.none()

    def get_queryset(self):
        return self.request.user.timeslots.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FilterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = FilterSerializer
    queryset = Filter.objects.none()

    def get_queryset(self):
        return self.request.user.filters.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        filter = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        connected_profiles = filter.notification_profiles.all()
        if connected_profiles:
            profiles = ", ".join([str(profile) for profile in connected_profiles])
            return Response(
                data="".join(
                    [
                        "Cannot delete this filter since it is in use in the notification profile(s): ",
                        profiles,
                        ".",
                    ]
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(filter)
        return Response(status=status.HTTP_204_NO_CONTENT)


# TODO: change HTTP method to GET, and get query data from URL
class FilterPreviewView(APIView):
    def post(self, request, format=None):
        """
        POST a filter, get a list of filtered incidents back

        Format:
        {
            "sourceSystemIds": [1, ..],
            "tags": ["some=tag", ..],
            "open": true,
            "acked": false,
            "stateful": true,
            "maxlevel": 3
        }

        Minimal format:
        {}
        """
        filter_dict = request.data
        serializer = FilterBlobSerializer(data=filter_dict)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        serializer = IncidentSerializer(QuerySetFilter.filtered_incidents(serializer.data), many=True)
        return Response(serializer.data)


filter_preview_view = FilterPreviewView.as_view()
