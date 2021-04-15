from django.urls import path

from rest_framework import routers

from . import views as views_V1
from .. import views


router = routers.SimpleRouter()
router.register(r"sources", views.SourceSystemViewSet)
router.register(r"source-types", views.SourceSystemTypeViewSet)
router.register(r"", views_V1.IncidentViewSetV1)

sourced_incident_list = views.SourceLockedIncidentViewSet.as_view({"get": "list", "post": "create"})

event_list = views.EventViewSet.as_view({"get": "list", "post": "create"})
event_detail = views.EventViewSet.as_view({"get": "retrieve"})

ack_list = views.AcknowledgementViewSet.as_view({"get": "list", "post": "create"})
ack_detail = views.AcknowledgementViewSet.as_view({"get": "retrieve"})


app_name = "incident"
urlpatterns = [
    path("mine/", sourced_incident_list, name="source_locked_incidents"),
    path("<int:incident_pk>/events/", event_list, name="incident-events"),
    path("<int:incident_pk>/events/<int:pk>/", event_detail, name="incident-event"),
    path("<int:incident_pk>/acks/", ack_list, name="incident-acks"),
    path("<int:incident_pk>/acks/<int:pk>/", ack_detail, name="incident-ack"),
    path("open/", views.OpenIncidentList.as_view(), name="incidents-open"),
    path("open+unacked/", views.OpenUnAckedIncidentList.as_view(), name="incidents-open-unacked"),
] + router.urls
