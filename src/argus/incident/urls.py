from django.urls import path

from . import views

app_name = "incident"
urlpatterns = [
    path("", views.IncidentList.as_view(), name="incidents"),
    path("<int:pk>/", views.IncidentDetail.as_view(), name="incident"),
    path("active/", views.ActiveIncidentList.as_view(), name="incidents-active"),
    path("<int:incident_pk>/active/", views.change_incident_active_view, name="incident-active"),
    path("source-types/", views.SourceSystemTypeList.as_view(), name="source-types"),
    path("sources/", views.SourceSystemList.as_view(), name="sources"),
    path("sources/<int:pk>/", views.SourceSystemDetail.as_view(), name="source"),
    path("metadata/", views.get_all_meta_data_view, name="incidents-metadata"),
]
