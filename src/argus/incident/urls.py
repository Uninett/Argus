from django.urls import path

from . import views

app_name = "incident"
urlpatterns = [
    path("", views.AlertList.as_view(), name="alerts"),
    path("<int:pk>", views.AlertDetail.as_view(), name="alert"),
    path("active/", views.ActiveAlertList.as_view(), name="alerts-active"),
    path("<int:alert_pk>/active", views.change_alert_active_view, name="alert-active"),
    path("source-types/", views.AlertSourceTypeList.as_view(), name="source-types"),
    path("sources/", views.AlertSourceList.as_view(), name="sources"),
    path("sources/<int:pk>/", views.AlertSourceDetail.as_view(), name="source"),
    path("metadata/", views.get_all_meta_data_view, name="alerts-metadata"),
]
