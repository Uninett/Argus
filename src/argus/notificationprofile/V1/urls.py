from django.urls import path

from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r"timeslots", views.TimeslotViewSetV1)
router.register(r"filters", views.FilterViewSetV1)
router.register(r"", views.NotificationProfileViewSetV1)

app_name = "notification-profile"
urlpatterns = [
    path("filterpreview/", views.filter_preview_view, name="filter-preview"),
] + router.urls
