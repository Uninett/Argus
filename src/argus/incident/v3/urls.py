from django.urls import path

from rest_framework import routers

from . import views


router = routers.SimpleRouter()
router.register(r"sources", views.SourceSystemViewSet)
router.register(r"", views.IncidentViewSet)

sourced_incident_list = views.SourceLockedIncidentViewSet.as_view({"get": "list", "post": "create"})

app_name = "incident"
urlpatterns = [
    path("mine/", sourced_incident_list, name="source_locked_incidents"),
] + router.urls
