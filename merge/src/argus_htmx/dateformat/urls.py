from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("names/", views.dateformat_names, name="dateformat-names"),
    path("change/", views.change_dateformat, name="change-dateformat"),
]
