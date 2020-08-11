"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.

Source:
https://channels.readthedocs.io/en/latest/deploying.html#run-protocol-servers
"""

import os

import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "argus.site.settings.dev")
django.setup()
application = get_default_application()
