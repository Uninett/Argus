"""Settings specific for Docker-based development environments"""
from .test_CI import *

# Allow all hosts, since all requests will typically come from outside the container
ALLOWED_HOSTS = ["*"]
