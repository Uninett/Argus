import json

from django.core import serializers
from django.db.models import QuerySet
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from aas.site.alert.models import Alert
from .models import User
from .models import NotificationProfile


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_profile_view(request, username):
    # json_result = json_utils.alert_hists_to_json(AlertHistory.objects.all())
    user = User.objects.filter(username=username)
    data: QuerySet = []
    profiles = NotificationProfile.objects.filter(pk=user[0].pk)
    alerts = Alert.objects.all()
    for alert in alerts:
        for profile in profiles:
            if isBetween(alert=alert, profile=profile):
                data.append(alert)
    json_result = json.dumps(serializers.serialize("json", data), indent=4)
    return HttpResponse(json_result, content_type="application/json")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification_profile_view(request):
    new_profile = NotificationProfile()
    username = request.POST.get("username")
    user = User.objects.filter(username=username)[0]
    interval_start = request.POST.get("start")
    interval_end = request.POST.get("end")
    new_profile.user = user
    new_profile.interval_start = interval_start
    new_profile.interval_stop = interval_end
    try:
        new_profile.save()
        return HttpResponse(status=200, content_type="application/json")
    except:
        return HttpResponse(status=400, content_type="application/json")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_notification_profile_view(request):
    profile = NotificationProfile.objects.filter(pk=request.POST.get("pk"))[0]
    profile.delete()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_profile_view(request, username):
    user = User.objects.filter(username=username)
    profiles = NotificationProfile.objects.filter(pk=user[0].pk)
    json_result = json.dumps(serializers.serialize("json", profiles), indent=4)
    return HttpResponse(json_result, content_type="application/json")



def isBetween(profile: NotificationProfile, alert: Alert):
    """
    :param profile: NotificationProfile
    :param alert: alert instance
    :return: Boolean
    True if the alert is within the given profile's desired interval
    True if noe interval is set for the profile
    False if the alert is outside of the given profile's desired interval
    """
    if profile.interval_start == None:
        return True

    if alert.timestamp.time() > profile.interval_start.time() and alert.timestamp.time() < profile.interval_stop.time():
        return True
    else:
        return False
