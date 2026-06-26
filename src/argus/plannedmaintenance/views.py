from datetime import timedelta

from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_rw_serializers import viewsets as rw_viewsets
from rest_framework import serializers, viewsets

from argus.drf.permissions import IsAdminOrReadOnly
from argus.filter import get_filter_backend
from argus.plannedmaintenance.models import MODIFICATION_WINDOW_PM, PlannedMaintenanceTask
from argus.plannedmaintenance.serializers import (
    RequestPlannedMaintenanceTaskSerializer,
    ResponsePlannedMaintenanceTaskSerializer,
)


filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter
FilterBlobSerializer = filter_backend.FilterBlobSerializer


@extend_schema_view(
    create=extend_schema(
        request=RequestPlannedMaintenanceTaskSerializer,
        responses={201: ResponsePlannedMaintenanceTaskSerializer},
    ),
    update=extend_schema(
        request=RequestPlannedMaintenanceTaskSerializer,
    ),
    partial_update=extend_schema(
        request=RequestPlannedMaintenanceTaskSerializer,
    ),
)
class PlannedMaintenanceTaskViewSet(rw_viewsets.ModelViewSet):
    permission_classes = permission_classes = [*viewsets.GenericViewSet.permission_classes, IsAdminOrReadOnly]
    serializer_class = ResponsePlannedMaintenanceTaskSerializer
    read_serializer_class = ResponsePlannedMaintenanceTaskSerializer
    write_serializer_class = RequestPlannedMaintenanceTaskSerializer
    queryset = PlannedMaintenanceTask.objects.all()
    http_method_names = ["get", "head", "post", "patch", "delete"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if not instance.future:
            hours = int(MODIFICATION_WINDOW_PM // timedelta(hours=1))
            raise serializers.ValidationError(
                f"This planned maintenance task is no longer modifiable as it ended more than {hours} hours ago."
            )
        instance.delete()
