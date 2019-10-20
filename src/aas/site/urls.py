"""aas URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework.authtoken import views as rest_views
from social_django.urls import extra

from . import views as aas_views
from aas.dataporten import views as dataporten_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('aas.site.auth.urls')),
    path('alert/', include('aas.site.alert.urls')),
    path('auth/', include('aas.site.auth.urls'))
]

urlpatterns += [
    path('api-token-auth/', rest_views.obtain_auth_token, name='api-token-auth'),

    # Overrides social_django's `complete` view
    re_path(r'^complete/(?P<backend>[^/]+){0}$'.format(extra), dataporten_views.login_wrapper, name='complete'),
    path('', include('social_django.urls', namespace='social')),
]
