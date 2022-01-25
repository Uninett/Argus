import json

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_rw_serializers import viewsets as rw_viewsets

from argus.drf.permissions import IsOwner
from argus.incident.serializers import IncidentSerializer
from ..models import Filter, NotificationProfile
from .serializers import (
    ResponseNotificationProfileSerializerV1,
    RequestNotificationProfileSerializerV1,
)
from ..serializers import FilterPreviewSerializer
from ..validators import validate_filter_string


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
        serializer = IncidentSerializer(notification_profile.filtered_incidents, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=FilterPreviewSerializer,
        responses=IncidentSerializer(many=True),
    )
    @action(methods=["post"], detail=False)
    def preview(self, request, **_):
        """
        POST a filterstring, get a list of filtered incidents back

        Format:
        {
            "sourceSystemIds": [1, ..],
            "tags": ["some=tag", ..],
        }

        Minimal format:
        {
            "sourceSystemIds": [],
            "tags": [],
        }

        Will eventually take over for the filterpreview endpoint
        """
        filter_string_dict = request.data
        try:
            validate_filter_string(filter_string_dict)
        except Exception as e:
            assert False, e

        filter_string_json = json.dumps(filter_string_dict)
        mock_filter = Filter(filter_string=filter_string_json)
        serializer = IncidentSerializer(mock_filter.filtered_incidents, many=True)
        return Response(serializer.data)
