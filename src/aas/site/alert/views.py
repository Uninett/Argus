import json

from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import FormView
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from aas.site.notificationprofile import views as notification_views
from .forms import AlertJsonForm
from .models import Alert, ProblemType, NetworkSystem, NetworkSystemType, ObjectType
from .serializers import AlertSerializer, ProblemTypeSerializer, NetworkSystemTypeSerializer, ObjectTypeSerializer


class AlertList(generics.ListCreateAPIView):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer

    def perform_create(self, serializer):
        created_alert = serializer.save()
        notification_views.send_notifications_to_users(created_alert)

def all_alerts_from_source_view(request, source_pk):
    data = serializers.serialize("json", Alert.objects.filter(source=source_pk))
    # Prettify the JSON data:
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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_meta_data_view(request):
    problem_types = ProblemTypeSerializer(ProblemType.objects.all(), many=True)
    network_system_types = NetworkSystemTypeSerializer(NetworkSystemType.objects.all(), many=True)
    object_types = ObjectTypeSerializer(ObjectType.objects.all(), many=True)
    data = {"problemTypes": problem_types.data, "networkSystemTypes":network_system_types.data, "objectTypes":object_types.data}
    return HttpResponse(json.dumps(data), content_type="application/json")

