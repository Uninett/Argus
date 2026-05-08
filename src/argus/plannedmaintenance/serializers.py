from rest_framework import serializers

from argus.auth.serializers import UsernameSerializer
from argus.filter.serializers import FilterSerializer
from argus.plannedmaintenance.models import PlannedMaintenanceTask
from argus.util.datetime_utils import LOCAL_INFINITY


class RequestPlannedMaintenanceTaskSerializer(serializers.ModelSerializer):
    end_time = serializers.DateTimeField(default=LOCAL_INFINITY, required=False, allow_null=True)

    class Meta:
        model = PlannedMaintenanceTask
        fields = [
            "start_time",
            "end_time",
            "description",
            "filters",
        ]

    def validate_end_time(self, value):
        if value is None:
            return LOCAL_INFINITY
        return value


class ResponsePlannedMaintenanceTaskSerializer(serializers.ModelSerializer):
    created_by = UsernameSerializer()
    filters = FilterSerializer(many=True)

    class Meta:
        model = PlannedMaintenanceTask
        fields = [
            "pk",
            "created_by",
            "created",
            "start_time",
            "end_time",
            "description",
            "filters",
        ]
