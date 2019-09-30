from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = 'alert'
urlpatterns = [
    path('create/', login_required(views.CreateAlertView.as_view()), name='create'),
]
