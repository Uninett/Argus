from argus.htmx.appconfig import APP_SETTINGS
from argus.site.utils import get_urlpatterns
from argus.util.app_utils import is_using_psa

urlpatterns = get_urlpatterns(APP_SETTINGS)

if is_using_psa():
    from argus.auth.psa.urls import urlpatterns as account_urlpatterns
else:
    from argus.htmx.auth.urls import urlpatterns as account_urlpatterns

urlpatterns = account_urlpatterns + urlpatterns
