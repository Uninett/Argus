from django.db.models import Q
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from argus.drf.permissions import IsOwner
from argus.filter import get_filter_backend
from argus.notificationprofile.media import api_safely_get_medium_object
from argus.notificationprofile.media.base import NotificationMedium
from argus.notificationprofile.models import DestinationConfig
from argus.notificationprofile.v2.serializers import DuplicateDestinationSerializer
from argus.notificationprofile.v2.views import (
    MediaViewSet as MediaViewSetV2,
    SchemaView as SchemaViewV2,
)

from .serializers import DestinationConfigSerializer

VERSION = "v3"


filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter
FilterBlobSerializer = filter_backend.FilterBlobSerializer


class SchemaView(SchemaViewV2):
    version = VERSION


class MediaViewSet(MediaViewSetV2):
    version = VERSION


@extend_schema_view(
    create=extend_schema(
        responses={201: DestinationConfigSerializer},
    ),
)
class DestinationConfigViewSet(viewsets.ModelViewSet):
    version = VERSION
    permission_classes = [*viewsets.ModelViewSet.permission_classes, IsOwner]
    serializer_class = DestinationConfigSerializer
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
            medium = api_safely_get_medium_object(destination.media.slug, self.version)
            medium.raise_if_not_deletable(destination)
        except NotificationMedium.NotDeletableError as e:
            raise ValidationError(str(e))
        else:
            return super().destroy(destination)

    def _is_destination_duplicate(self, destination):
        other_destinations = DestinationConfig.objects.filter(media=destination.media).filter(
            ~Q(user_id=destination.user.id)
        )
        medium = api_safely_get_medium_object(destination.media_id, self.version)
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
