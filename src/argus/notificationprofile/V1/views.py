from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_rw_serializers import viewsets as rw_viewsets

from argus.drf.permissions import IsOwner
from argus.filter.queryset_filters import QuerySetFilter
from argus.filter.V1.serializers import (
    FilterSerializerV1,
    FilterBlobSerializerV1,
    FilterPreviewSerializer,
)
from argus.incident.serializers import IncidentSerializer
from ..models import Filter, NotificationProfile
from .serializers import (
    ResponseNotificationProfileSerializerV1,
    RequestNotificationProfileSerializerV1,
)


class FilterViewSetV1(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = FilterSerializerV1
    queryset = Filter.objects.none()

    def get_queryset(self):
        return self.request.user.filters.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        filter = self.get_queryset().get(pk=self.kwargs["pk"])
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


@extend_schema_view(
    create=extend_schema(
        request=RequestNotificationProfileSerializerV1,
        responses={201: ResponseNotificationProfileSerializerV1},
    ),
    update=extend_schema(
        request=RequestNotificationProfileSerializerV1,
    ),
    partial_update=extend_schema(
        request=RequestNotificationProfileSerializerV1,
    ),
)
class NotificationProfileViewSetV1(rw_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ResponseNotificationProfileSerializerV1
    read_serializer_class = ResponseNotificationProfileSerializerV1
    write_serializer_class = RequestNotificationProfileSerializerV1
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
        request=FilterPreviewSerializer,
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
        serializer = FilterBlobSerializerV1(data=filter_dict)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        serializer = IncidentSerializer(QuerySetFilter.filtered_incidents(serializer.data), many=True)
        return Response(serializer.data)
