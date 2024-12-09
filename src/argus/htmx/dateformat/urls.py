from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("change/", views.change_dateformat, name="change-dateformat"),
]
