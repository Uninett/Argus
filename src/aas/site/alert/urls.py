from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = 'alert'
urlpatterns = [
    path('all/', login_required(views.all_alerts_view), name='all'),
    path('create/', login_required(views.CreateAlertView.as_view()), name='create'),
]
