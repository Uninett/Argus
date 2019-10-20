from django.core import serializers
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from aas.site.alert.models import Alert
from .models import NotificationProfile
from .serializers import NotificationProfileSerializer


class NotificationProfileView(APIView):
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notification_profiles = request.user.notification_profiles.all()
        serializer = NotificationProfileSerializer(notification_profiles, many=True)
        return Response(serializer.data)

    def post(self, request):
        new_profile = NotificationProfile()
        new_profile.user = request.user
        new_profile.interval_start = request.POST.get("start")
        new_profile.interval_stop = request.POST.get("end")
        new_profile.save()

        serializer = NotificationProfileSerializer(new_profile)
        return Response(serializer.data)

    def delete(self, request, profile_id):
        profile = self.get_object(profile_id)
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get_object(pk):
        try:
            return NotificationProfile.objects.get(pk=pk)
        except NotificationProfile.DoesNotExist:
            raise Http404


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
