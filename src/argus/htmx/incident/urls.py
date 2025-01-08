from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.incident_list, name="incident-list"),
    path("<int:pk>/", views.incident_detail, name="incident-detail"),
    path("update/<str:action>/", views.incident_update, name="incident-update"),
    path("filter/", views.filter_form, name="incident-filter"),
]
