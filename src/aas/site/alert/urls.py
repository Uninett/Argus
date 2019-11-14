from django.urls import path

from . import views

app_name = "alert"
urlpatterns = [
    path("", views.AlertList.as_view()),
    path("<int:pk>", views.AlertDetail.as_view()),

    path("active/", views.ActiveAlertList.as_view()),
    path("<int:alert_pk>/active", views.change_alert_active_view),

    path("source/<int:source_pk>", views.all_alerts_from_source_view, name="source"),
    path("metadata/", views.get_all_meta_data_view),
    path("preview/", views.preview),
]
