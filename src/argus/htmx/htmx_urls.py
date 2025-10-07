from argus.htmx.appconfig import APP_SETTINGS
from argus.site.utils import get_urlpatterns
from argus.util.app_utils import is_using_psa, is_using_allauth


account_urlpatterns = []
urlpatterns = get_urlpatterns(APP_SETTINGS)

if is_using_psa():
    from argus.auth.psa.urls import urlpatterns as account_urlpatterns
elif is_using_allauth():
    from argus.auth.allauth.urls import urlpatterns as account_urlpatterns
else:
    from argus.htmx.auth.urls import urlpatterns as account_urlpatterns

urlpatterns = account_urlpatterns + urlpatterns
