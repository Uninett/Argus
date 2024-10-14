from argus.site.urls import urlpatterns

from .spa_urls import urlpatterns as spa_urlpatterns


urlpatterns += spa_urlpatterns
