from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated

from aas.site.alert.models import Alert
from .permissions import IsOwner
from .serializers import FilterSerializer, NotificationProfileSerializer, TimeSlotSerializer


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


@api_view(['GET'])
def alerts_filtered_by_notification_profile_view(request, notification_profile_pk):
    # Go through user to ensure that the user owns the requested notification profile
    profile_filters = request.user.notification_profiles.get(pk=notification_profile_pk).filters.all()
    alert_query = Q()
    # TODO: filter alerts with notification profiles' filters
    data = Alert.objects.filter(alert_query)
    json_result = serializers.serialize("json", data)
    return HttpResponse(json_result, content_type="application/json")


class TimeSlotList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeSlotSerializer

    def get_queryset(self):
        return self.request.user.time_slots.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TimeSlotDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeSlotSerializer

    def get_queryset(self):
        return self.request.user.time_slots.all()


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
