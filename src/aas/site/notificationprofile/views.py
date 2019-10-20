from django.core import serializers
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from aas.site.alert.models import Alert
from .models import NotificationProfile


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification_profile_view(request):
    new_profile = NotificationProfile()
    new_profile.user = request.user
    new_profile.interval_start = request.POST.get("start")
    new_profile.interval_stop = request.POST.get("end")
    new_profile.save()

    json_result = serializers.serialize("json", [new_profile])
    return HttpResponse(json_result, content_type="application/json")


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification_profile_view(request, profile_id):
    profile_to_delete = NotificationProfile.objects.get(pk=profile_id)
    json_result = serializers.serialize("json", [profile_to_delete])
    profile_to_delete.delete()
    return HttpResponse(json_result, content_type="application/json")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_profiles_view(request):
    json_result = serializers.serialize("json", request.user.notification_profiles.all())
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
