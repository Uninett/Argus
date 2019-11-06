from typing import List

from django.core import serializers
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from aas.site.alert.models import Alert
from aas.site.auth.models import User
from . import notification_media
from .models import NotificationProfile, Filter
from .permissions import IsOwner

from .serializers import NotificationProfileSerializer, TimeSlotGroupSerializer, TimeSlotSerializer
from .serializers import NotificationProfileSerializer, FilterSerializer


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
def notification_profile_alerts_view(request):
    profiles = request.user.notification_profiles.all()
    data = []
    # TODO: do this with a queryset
    for alert in Alert.objects.all():
        for profile in profiles:
            if is_between(alert=alert, profile=profile):
                data.append(alert)
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


class TimeSlotList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeSlotSerializer

    def get_queryset(self):
        return self.request.user.time_slot.all()

    def perform_create(self, serializer):
        serializer.save()


class FilterList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FilterSerializer

    def get_queryset(self):
        return self.request.user.filters.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def is_between(profile: NotificationProfile, alert: Alert):
    """
    :param profile: NotificationProfile
    :param alert: alert instance
    :return: Boolean
    True if the alert is within the given profile's desired interval
    False if the alert is outside of the given profile's desired interval
    """
    # TODO: update with TimeSlotGroup's time slot times
    return profile.interval_start.time() < alert.timestamp.time() < profile.interval_stop.time()


def send_notifications_to_users(alert: Alert):
    for profile in NotificationProfile.objects.select_related('user'):
        if is_between(profile, alert):
            send_notification(profile.user, profile, alert)


def send_notification(user: User, profile: NotificationProfile, alert: Alert):
    media = get_notification_media(list(profile.media))
    for medium in media:
        if medium is not None:
            medium.send(alert, user)


def get_notification_media(model_representations: List[str]):
    return (notification_media.get_medium(representation) for representation in model_representations)
