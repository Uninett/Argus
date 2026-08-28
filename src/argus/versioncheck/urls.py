from django.urls import path

from .views import check_for_new_version


urlpatterns = [
    path("check", check_for_new_version, name="check-for-new-version"),
]
