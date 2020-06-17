import json

from django.core import serializers
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from aas.notificationprofile.notification_media import send_notifications_to_users
from . import mappings
from .models import (
    ActiveAlert,
    Alert,
    AlertSource,
    ObjectType,
    ParentObject,
    ProblemType,
)
from .parsers import StackedJSONParser
from .serializers import (
    AlertSerializer,
    AlertSourceSerializer,
    ObjectTypeSerializer,
    ParentObjectSerializer,
    ProblemTypeSerializer,
)


class AlertList(generics.ListCreateAPIView):
    queryset = Alert.prefetch_related_fields(
        Alert.objects.select_related("active_state")
    )
    parser_classes = [StackedJSONParser]
    serializer_class = AlertSerializer

    def post(self, request, *args, **kwargs):
        created_alerts = [
            mappings.create_alert_from_json(
                json_dict, AlertSource.NAV
            )  # TODO: interpret alert source type from alerts' source IP?
            for json_dict in request.data
        ]

        for created_alert in created_alerts:
            send_notifications_to_users(created_alert)

        if len(created_alerts) == 1:
            serializer = AlertSerializer(created_alerts[0])
        else:
            serializer = AlertSerializer(created_alerts, many=True)
        return Response(serializer.data)


class AlertDetail(generics.RetrieveAPIView):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer


class ActiveAlertList(generics.ListAPIView):
    serializer_class = AlertSerializer

    def get_queryset(self):
        return Alert.prefetch_related_fields(Alert.get_active_alerts())


@api_view(["PUT"])
def change_alert_active_view(request, alert_pk):
    if type(request.data) is not dict:
        raise ValidationError("The request body must contain JSON.")

    new_active_state = request.data.get("active")
    if new_active_state is None or type(new_active_state) is not bool:
        raise ValidationError(
            "Field 'active' with a boolean value is missing from the request body."
        )

    alert = Alert.objects.get(pk=alert_pk)
    if new_active_state:
        ActiveAlert.objects.get_or_create(alert=alert)
    else:
        if hasattr(alert, "active_state"):
            alert.active_state.delete()

    alert = Alert.objects.get(
        pk=alert_pk
    )  # re-fetch the alert to get updated state after creating/deleting ActiveAlert object
    serializer = AlertSerializer(alert)
    return Response(serializer.data)


# TODO: remove, as `filter_preview_view()` does the same and more?
def all_alerts_from_source_view(request, source_pk):
    data = serializers.serialize("json", Alert.objects.filter(source=source_pk))
    # Prettify the JSON data:
    json_result = json.dumps(json.loads(data), indent=4)
    return HttpResponse(json_result, content_type="application/json")


@api_view(["GET"])
def get_all_meta_data_view(request):
    alert_sources = AlertSourceSerializer(AlertSource.objects.all(), many=True)
    object_types = ObjectTypeSerializer(ObjectType.objects.all(), many=True)
    parent_objects = ParentObjectSerializer(ParentObject.objects.all(), many=True)
    problem_types = ProblemTypeSerializer(ProblemType.objects.all(), many=True)
    data = {
        "alertSources": alert_sources.data,
        "objectTypes": object_types.data,
        "parentObjects": parent_objects.data,
        "problemTypes": problem_types.data,
    }
    return Response(data)
