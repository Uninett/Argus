from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.ThemeListView.as_view(), name="theme-list"),
]
