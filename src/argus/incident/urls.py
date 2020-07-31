from django.urls import path

from . import views

incident_list = views.IncidentViewSet.as_view({"get": "list", "post": "create"})
incident_detail = views.IncidentViewSet.as_view({"get": "retrieve",})
incident_active = views.IncidentViewSet.as_view({"put": "active",})
incident_ticket_url = views.IncidentViewSet.as_view({"put": "ticket_url",})

app_name = "incident"
urlpatterns = [
    path("active/", views.ActiveIncidentList.as_view(), name="incidents-active"),
    path("", incident_list, name="alerts"),
    path("<int:pk>", incident_detail, name="alert"),
    path("<int:pk>/active", incident_active, name="alert-active"),
    path("<int:pk>/ticket_url", incident_ticket_url, name="alert-ticket-url"),
    path("source-types/", views.SourceSystemTypeList.as_view(), name="source-types"),
    path("sources/", views.SourceSystemList.as_view(), name="sources"),
    path("sources/<int:pk>/", views.SourceSystemDetail.as_view(), name="source"),
    path("metadata/", views.get_all_meta_data_view, name="incidents-metadata"),
]
