from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.user_preferences, name="user-preferences"),
    path("incident-table-preview/", views.incident_table_preview, name="incident-table-preview"),
    path("update/<str:namespace>/", views.update_preferences, name="update-preferences"),
]
