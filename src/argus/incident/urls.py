from django.urls import path

from . import views


incident_list = views.IncidentViewSet.as_view({"get": "list", "post": "create"})
incident_detail = views.IncidentViewSet.as_view({"get": "retrieve", "patch": "partial_update"})

event_list = views.EventViewSet.as_view({"get": "list", "post": "create"})
event_detail = views.EventViewSet.as_view({"get": "retrieve"})

app_name = "incident"
urlpatterns = [
    path("", incident_list, name="incidents"),
    path("legacy/", views.IncidentCreate_legacy.as_view()),  # TODO: remove once it's not in use anymore
    path("<int:pk>/", incident_detail, name="incident"),
    path("<int:incident_pk>/events/", event_list, name="incident-events"),
    path("<int:incident_pk>/events/<int:pk>/", event_detail, name="incident-event"),
    path("active/", views.ActiveIncidentList.as_view(), name="incidents-active"),
    path("source-types/", views.SourceSystemTypeList.as_view(), name="source-types"),
    path("sources/", views.SourceSystemList.as_view(), name="sources"),
    path("sources/<int:pk>/", views.SourceSystemDetail.as_view(), name="source"),
    path("metadata/", views.get_all_meta_data_view, name="incidents-metadata"),
]
