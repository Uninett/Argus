from django.urls import path

from rest_framework import routers

from . import views


router = routers.SimpleRouter()
router.register(r"sources", views.SourceSystemViewSet)
router.register(r"source-types", views.SourceSystemTypeViewSet)
router.register(r"", views.IncidentViewSet)

sourced_incident_list = views.SourceLockedIncidentViewSet.as_view({"get": "list", "post": "create"})

all_events_list = views.AllEventsViewSet.as_view({"get": "list"})
event_list = views.EventViewSet.as_view({"get": "list", "post": "create"})
event_detail = views.EventViewSet.as_view({"get": "retrieve"})
events_bulk_list = views.BulkEventViewSet.as_view({"post": "create"})

ack_list = views.AcknowledgementViewSet.as_view({"get": "list", "post": "create"})
ack_detail = views.AcknowledgementViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update"})
acks_bulk_list = views.BulkAcknowledgementViewSet.as_view({"post": "create"})

tag_list = views.IncidentTagViewSet.as_view({"get": "list", "post": "create"})
tag_detail = views.IncidentTagViewSet.as_view({"get": "retrieve", "delete": "destroy"})

ticket_plugin_detail = views.TicketPluginViewSet.as_view({"put": "update"})
ticket_url_bulk_list = views.BulkTicketUrlViewSet.as_view({"post": "create"})

app_name = "incident"
urlpatterns = [
    path("acks/bulk/", acks_bulk_list, name="incident-acks-bulk"),
    path("events/", all_events_list, name="events"),
    path("events/bulk/", events_bulk_list, name="incident-events-bulk"),
    path("mine/", sourced_incident_list, name="source_locked_incidents"),
    path("ticket_url/bulk/", ticket_url_bulk_list, name="incident-ticket-url-bulk"),
    path("<int:incident_pk>/events/", event_list, name="incident-events"),
    path("<int:incident_pk>/events/<int:pk>/", event_detail, name="incident-event"),
    path("<int:incident_pk>/acks/", ack_list, name="incident-acks"),
    path("<int:incident_pk>/acks/<int:pk>/", ack_detail, name="incident-ack"),
    path("<int:incident_pk>/tags/", tag_list, name="incident-tags"),
    path("<int:incident_pk>/tags/<str:tag>/", tag_detail, name="incident-tag"),
    path("<int:incident_pk>/automatic-ticket/", ticket_plugin_detail, name="incident-ticket-plugin"),
] + router.urls
