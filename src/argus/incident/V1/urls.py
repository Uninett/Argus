from django.urls import path
from rest_framework import routers

from .. import views
from . import views as views_V1

router = routers.SimpleRouter()
router.register(r"sources", views.SourceSystemViewSet)
router.register(r"source-types", views.SourceSystemTypeViewSet)
router.register(r"", views_V1.IncidentViewSetV1)

sourced_incident_list = views_V1.SourceLockedIncidentViewSetV1.as_view({"get": "list", "post": "create"})

event_list = views.EventViewSet.as_view({"get": "list", "post": "create"})
event_detail = views.EventViewSet.as_view({"get": "retrieve"})

ack_list = views_V1.AcknowledgementViewSetV1.as_view({"get": "list", "post": "create"})
ack_detail = views_V1.AcknowledgementViewSetV1.as_view({"get": "retrieve", "put": "update", "patch": "partial_update"})

tag_list = views.IncidentTagViewSet.as_view({"get": "list", "post": "create"})
tag_detail = views.IncidentTagViewSet.as_view({"get": "retrieve", "delete": "destroy"})

app_name = "incident"
urlpatterns = [
    path("mine/", sourced_incident_list, name="source_locked_incidents"),
    path("<int:incident_pk>/events/", event_list, name="incident-events"),
    path("<int:incident_pk>/events/<int:pk>/", event_detail, name="incident-event"),
    path("<int:incident_pk>/acks/", ack_list, name="incident-acks"),
    path("<int:incident_pk>/acks/<int:pk>/", ack_detail, name="incident-ack"),
    path("<int:incident_pk>/tags/", tag_list, name="incident-tags"),
    path("<int:incident_pk>/tags/<str:tag>/", tag_detail, name="incident-tag"),
    path("open/", views_V1.OpenIncidentListV1.as_view(), name="incidents-open"),
    path("open+unacked/", views_V1.OpenUnAckedIncidentListV1.as_view(), name="incidents-open-unacked"),
] + router.urls
