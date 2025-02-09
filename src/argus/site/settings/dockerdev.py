"""Settings specific for Docker-based development environments"""

from .dev import *  # noqa: F401, F403

# Allow all hosts, since all requests will typically come from outside the container
ALLOWED_HOSTS = ["*"]
