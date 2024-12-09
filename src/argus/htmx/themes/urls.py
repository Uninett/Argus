from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("change/", views.change_theme, name="change-theme"),
]
