from argus.spa.settings import *

# Beware: setting this to something else in production has security implications
INTERNAL_IPS = []  # Don't alter me, please
EMAIL_PORT = get_int_env("EMAIL_PORT", 587)
EMAIL_USE_TLS = get_bool_env("EMAIL_USE_TLS", default=True)
