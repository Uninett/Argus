from django.urls import path

from . import views


incident_list = views.IncidentViewSet.as_view({"get": "list", "post": "create"})
incident_detail = views.IncidentViewSet.as_view({"get": "retrieve", "patch": "partial_update"})
incident_active = views.IncidentViewSet.as_view({"put": "active",})
incident_ticket_url = views.IncidentViewSet.as_view({"put": "ticket_url",})

app_name = "incident"
urlpatterns = [
    path("", incident_list, name="incidents"),
    path("legacy/", views.IncidentCreate_legacy.as_view()),  # TODO: remove once it's not in use anymore
    path("<int:pk>/", incident_detail, name="incident"),
    path("<int:pk>/active/", incident_active, name="incident-active"),
    path("<int:pk>/ticket_url/", incident_ticket_url, name="incident-ticket-url"),
    path("active/", views.ActiveIncidentList.as_view(), name="incidents-active"),
    path("source-types/", views.SourceSystemTypeList.as_view(), name="source-types"),
    path("sources/", views.SourceSystemList.as_view(), name="sources"),
    path("sources/<int:pk>/", views.SourceSystemDetail.as_view(), name="source"),
    path("metadata/", views.get_all_meta_data_view, name="incidents-metadata"),
]
