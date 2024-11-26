from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("names/", views.theme_names, name="theme-names"),
    path("change/", views.change_theme, name="change-theme"),
]
