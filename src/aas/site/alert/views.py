import json
import datetime

from django.core import serializers
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import FormView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ..auth.models import User
from . import json_utils
#from .utils import isBetween
from .forms import AlertJsonForm
from .models import Alert, Notification_profile


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_alerts_view(request):
    # json_result = json_utils.alert_hists_to_json(AlertHistory.objects.all())
    data = serializers.serialize("json", Alert.objects.all())
    json_result = json.dumps(json.loads(data), indent=4)
    return HttpResponse(json_result, content_type="application/json")


def all_alerts_from_source_view(request, source_pk):
    data = serializers.serialize("json", Alert.objects.filter(source=source_pk))
    json_result = json.dumps(json.loads(data), indent=4)
    return HttpResponse(json_result, content_type="application/json")


class CreateAlertView(FormView):
    template_name = "alert/create_alert.html"
    form_class = AlertJsonForm

    def form_valid(self, form):
        """ TODO: temporarily disabled until JSON parsing has been implemented for the new data model
        json_string = form.cleaned_data["json"]
        alert_hist = json_utils.json_to_alert_hist(json_string)
        alert_hist.save()
        """
        # Redirect back to same form page
        return HttpResponseRedirect(self.request.path_info)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notification_profile_view(request):
    # json_result = json_utils.alert_hists_to_json(AlertHistory.objects.all())

    username = request.POST.get("username")
    user = User.objects.filter(username=username)
    data: QuerySet = []
    profiles = Notification_profile.objects.filter(pk=user[0].pk)
    alerts = Alert.objects.all()
    for alert in alerts:
        for profile in profiles:
            if isBetween(alert=alert, profile=profile):
                data.append(alert)
    json_result = json.dumps(serializers.serialize("json", data), indent=4)
    response = {"alerts": json_result }
    return HttpResponse(json.dumps(response), content_type="application/json")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification_profile_view(request):
    new_profile = Notification_profile()
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
    profile = Notification_profile.objects.filter(pk=request.POST.get("pk"))[0]
    profile.delete()




def isBetween(profile: Notification_profile, alert: Alert):
    """
    :param profile: Notification_profile
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
