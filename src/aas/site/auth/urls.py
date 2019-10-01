from django.contrib.auth import views

from django.urls import path

app_name = 'auth'
urlpatterns = [
    path('login/',
         views.LoginView.as_view(template_name='auth/login.html', redirect_authenticated_user=True),
         name='login'),

    path('logout/',
         views.LogoutView.as_view(),
         name='logout'),
]
