from django.core import serializers
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from aas.site.alert.models import Alert
from .models import NotificationProfile
from .permissions import IsOwner
from .serializers import NotificationProfileSerializer


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


def is_between(profile: NotificationProfile, alert: Alert):
    """
    :param profile: NotificationProfile
    :param alert: alert instance
    :return: Boolean
    True if the alert is within the given profile's desired interval
    True if noe interval is set for the profile
    False if the alert is outside of the given profile's desired interval
    """
    if profile.interval_start is None:
        return True

    if profile.interval_start.time() < alert.timestamp.time() < profile.interval_stop.time():
        return True
    else:
        return False
