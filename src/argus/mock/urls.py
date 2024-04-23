from django.urls import path

from . import views


app_name = "guest_mock"
urlpatterns = [
    path("detail/<int:pk>/", views.mock_detail, name="mock_detail"),
]
