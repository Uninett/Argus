from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "alert"
urlpatterns = [
    path("all/", views.all_alerts_view, name="all"),
    # path("create/", login_required(views.CreateAlertView.as_view()), name="create"),
    path("source/<int:source_pk>/", views.all_alerts_from_source_view, name="source"),
    path("notification_profile/<username>", views.notification_profile_view, name="notification_profile"),
    path("create_notification_profile/", views.create_notification_profile_view, name="create_notification_profile"),
    path("delete_notification_profile/", views.delete_notification_profile_view, name="delete_notification_profile"),
    path("get_notification_profile/<username>", views.get_notification_profile_view, name="get_notification_profile"),
]
