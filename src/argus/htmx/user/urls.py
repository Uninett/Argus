from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.user_preferences, name="user-preferences"),
    path("page_size/change/", views.change_page_size, name="change-page-size"),
]
