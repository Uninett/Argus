from django.db.models import Q
from django.shortcuts import get_object_or_404

from drf_rw_serializers import viewsets as rw_viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from argus.drf.permissions import IsOwner
from argus.filter import get_filter_backend
from argus.notificationprofile.media import safely_get_medium_object
from argus.notificationprofile.media.base import NotificationMedium
from argus.notificationprofile.models import DestinationConfig
from argus.notificationprofile.v2.serializers import DuplicateDestinationSerializer
from argus.notificationprofile.v2.views import (
    MediaViewSet as MediaViewSetV2,
    SchemaView as SchemaViewV2,
)

from .serializers import RequestDestinationConfigSerializer, ResponseDestinationConfigSerializer

VERSION = "v3"


filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter
FilterBlobSerializer = filter_backend.FilterBlobSerializer


class SchemaView(SchemaViewV2):
    pass


class MediaViewSet(MediaViewSetV2):
    pass


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
    permission_classes = [*rw_viewsets.ModelViewSet.permission_classes, IsOwner]
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
            medium = safely_get_medium_object(destination.media.slug)
            medium.raise_if_not_deletable(destination)
        except NotificationMedium.NotDeletableError as e:
            raise ValidationError(str(e))
        else:
            return super().destroy(destination)

    def _is_destination_duplicate(self, destination):
        other_destinations = DestinationConfig.objects.filter(media=destination.media).filter(
            ~Q(user_id=destination.user.id)
        )
        medium = safely_get_medium_object(destination.media_id)
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
