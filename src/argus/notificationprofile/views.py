import json

from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from argus.drf.permissions import IsOwner
from argus.incident.serializers import IncidentSerializer
from .models import Filter, NotificationProfile
from .serializers import (
    FilterSerializer,
    NotificationProfileSerializer,
    TimeslotSerializer,
)
from .validators import validate_filter_string


class NotificationProfileList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = NotificationProfileSerializer

    def get_queryset(self):
        return self.request.user.notification_profiles.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = NotificationProfileSerializer

    def get_queryset(self):
        return self.request.user.notification_profiles.all()


@api_view(["GET"])
def incidents_filtered_by_notification_profile_view(request, notification_profile_pk):
    try:
        # Go through user to ensure that the user owns the requested notification profile
        notification_profile = request.user.notification_profiles.get(pk=notification_profile_pk)
    except NotificationProfile.DoesNotExist:
        raise ValidationError(f"Notification profile with pk={notification_profile_pk} does not exist.")

    serializer = IncidentSerializer(notification_profile.filtered_incidents, many=True)
    return Response(serializer.data)


class TimeslotList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeslotSerializer

    def get_queryset(self):
        return self.request.user.timeslots.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TimeslotDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeslotSerializer

    def get_queryset(self):
        return self.request.user.timeslots.all()


class FilterList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = FilterSerializer

    def get_queryset(self):
        return self.request.user.filters.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FilterDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = FilterSerializer

    def get_queryset(self):
        return self.request.user.filters.all()


# TODO: change HTTP method to GET, and get query data from URL
@api_view(["POST"])
def filter_preview_view(request):
    filter_string_dict = request.data
    validate_filter_string(filter_string_dict)

    filter_string_json = json.dumps(filter_string_dict)
    mock_filter = Filter(filter_string=filter_string_json)
    serializer = IncidentSerializer(mock_filter.filtered_incidents, many=True)
    return Response(serializer.data)
