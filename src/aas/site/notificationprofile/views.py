from typing import List

from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from aas.site.alert.models import Alert
from aas.site.auth.models import User
from . import notification_media
from .models import NotificationProfile
from .permissions import IsOwner
from .serializers import FilterSerializer, NotificationProfileSerializer, TimeSlotGroupSerializer


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
@permission_classes([IsAuthenticated])
def alerts_filtered_by_notification_profile_view(request, notification_profile_pk):
    # Go through user to ensure that the user owns the requested notification profile
    profile_filters = request.user.notification_profiles.get(pk=notification_profile_pk).filters.all()
    alert_query = Q()
    # TODO: filter alerts with notification profiles' filters
    data = Alert.objects.filter(alert_query)
    json_result = serializers.serialize("json", data)
    return HttpResponse(json_result, content_type="application/json")


class TimeSlotGroupList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeSlotGroupSerializer

    def get_queryset(self):
        return self.request.user.time_slot_groups.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TimeSlotGroupDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeSlotGroupSerializer

    def get_queryset(self):
        return self.request.user.time_slot_groups.all()


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


def send_notifications_to_users(alert: Alert):
    for profile in NotificationProfile.objects.select_related('user'):
        if profile.alert_fits(alert):
            send_notification(profile.user, profile, alert)


def send_notification(user: User, profile: NotificationProfile, alert: Alert):
    media = get_notification_media(list(profile.media))
    for medium in media:
        if medium is not None:
            medium.send(alert, user)


def get_notification_media(model_representations: List[str]):
    return (notification_media.get_medium(representation) for representation in model_representations)
