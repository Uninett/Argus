# from django.urls import path

from rest_framework import routers

from . import views


router = routers.SimpleRouter()
router.register(r"sources", views.SourceSystemViewSet)
router.register(r"", views.IncidentViewSet)

app_name = "incident"
urlpatterns = router.urls
