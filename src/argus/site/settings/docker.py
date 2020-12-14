from .dev import *

# Allow all hosts, since all requests will typically come from outside the container
ALLOWED_HOSTS = ["*"]
