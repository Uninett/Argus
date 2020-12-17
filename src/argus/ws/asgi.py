"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.

Source:
https://channels.readthedocs.io/en/latest/deploying.html#run-protocol-servers
"""
import django
from channels.routing import get_default_application

django.setup()
application = get_default_application()
