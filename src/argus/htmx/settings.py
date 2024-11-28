from argus.site.settings.backend import *
from argus.site.utils import update_settings

from argus.htmx.appconfig import APP_SETTINGS


update_settings(globals(), APP_SETTINGS)

ROOT_URLCONF = "argus.htmx.root_urls"
