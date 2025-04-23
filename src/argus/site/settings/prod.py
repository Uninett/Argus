from argus.site.utils import update_settings
from argus.site.settings.backend import *
from argus.htmx.appconfig import APP_SETTINGS

update_settings(globals(), APP_SETTINGS)

ROOT_URLCONF = "argus.htmx.root_urls"

# Beware: setting this to something else in production has security implications
INTERNAL_IPS = []  # Don't alter me, please
EMAIL_PORT = get_int_env("EMAIL_PORT", 587)
EMAIL_USE_TLS = get_bool_env("EMAIL_USE_TLS", default=True)
