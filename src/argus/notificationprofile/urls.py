from django.urls import path, include

from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r"timeslots", views.TimeslotViewSet)
router.register(r"media", views.MediaViewSet)
router.register(r"filters", views.FilterViewSet)
router.register(r"destinations", views.DestinationConfigViewSet)
router.register(r"", views.NotificationProfileViewSet)

app_name = "notification-profile"
urlpatterns = [
    path("filterpreview/", views.filter_preview_view, name="filter-preview"),
] + router.urls
