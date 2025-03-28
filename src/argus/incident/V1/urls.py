from django.urls import path

from rest_framework import routers

from . import views


router = routers.SimpleRouter()
router.register(r"sources", views.SourceSystemViewSetV1)
router.register(r"source-types", views.SourceSystemTypeViewSetV1)
router.register(r"", views.IncidentViewSetV1)

sourced_incident_list = views.SourceLockedIncidentViewSetV1.as_view({"get": "list", "post": "create"})

event_list = views.EventViewSetV1.as_view({"get": "list", "post": "create"})
event_detail = views.EventViewSetV1.as_view({"get": "retrieve"})

ack_list = views.AcknowledgementViewSetV1.as_view({"get": "list", "post": "create"})
ack_detail = views.AcknowledgementViewSetV1.as_view({"get": "retrieve", "put": "update", "patch": "partial_update"})

tag_list = views.IncidentTagViewSetV1.as_view({"get": "list", "post": "create"})
tag_detail = views.IncidentTagViewSetV1.as_view({"get": "retrieve", "delete": "destroy"})

app_name = "incident"
urlpatterns = [
    path("mine/", sourced_incident_list, name="source_locked_incidents"),
    path("<int:incident_pk>/events/", event_list, name="incident-events"),
    path("<int:incident_pk>/events/<int:pk>/", event_detail, name="incident-event"),
    path("<int:incident_pk>/acks/", ack_list, name="incident-acks"),
    path("<int:incident_pk>/acks/<int:pk>/", ack_detail, name="incident-ack"),
    path("<int:incident_pk>/tags/", tag_list, name="incident-tags"),
    path("<int:incident_pk>/tags/<str:tag>/", tag_detail, name="incident-tag"),
    path("open/", views.OpenIncidentListV1.as_view(), name="incidents-open"),
    path("open+unacked/", views.OpenUnAckedIncidentListV1.as_view(), name="incidents-open-unacked"),
] + router.urls
