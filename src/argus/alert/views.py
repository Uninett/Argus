from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from argus.notificationprofile.notification_media import send_notifications_to_users
from . import mappings
from .forms import AddAlertSourceForm
from .models import (
    ActiveAlert,
    Alert,
    AlertSource,
    AlertSourceType,
    ObjectType,
    ParentObject,
    ProblemType,
)
from .parsers import StackedJSONParser
from .permissions import IsOwnerOrReadOnly, IsSuperuserOrReadOnly
from .serializers import (
    AlertSerializer,
    AlertSourceSerializer,
    AlertSourceTypeSerializer,
    ObjectTypeSerializer,
    ParentObjectSerializer,
    ProblemTypeSerializer,
)


class AlertSourceTypeList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlertSourceTypeSerializer
    queryset = AlertSourceType.objects.all()


class AlertSourceList(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrReadOnly]
    queryset = AlertSource.objects.all()

    def get_serializer_class(self):
        # If method is POST, let `create()` below handle validation and serialization
        return None if self.request.method == "POST" else AlertSourceSerializer

    def create(self, request, *args, **kwargs):
        # Reuse the logic in the form that's used on the admin page
        form = AddAlertSourceForm(request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        alert_source = form.save()
        serializer = AlertSourceSerializer(alert_source)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class AlertSourceDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = AlertSource.objects.all()
    serializer_class = AlertSourceSerializer


class AlertList(generics.ListCreateAPIView):
    queryset = Alert.objects.prefetch_default_related().select_related("active_state")
    parser_classes = [StackedJSONParser]
    serializer_class = AlertSerializer

    def post(self, request, *args, **kwargs):
        # TODO: replace with deserializing JSON for one alert per request, with data that's already been mapped (once glue services have been implemented)
        created_alerts = [
            mappings.create_alert_from_json(
                json_dict, "NAV"
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
        return Alert.objects.active().prefetch_default_related()


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


@api_view(["GET"])
def get_all_meta_data_view(request):
    alert_sources = AlertSourceSerializer(
        AlertSource.objects.select_related("type"), many=True
    )
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
