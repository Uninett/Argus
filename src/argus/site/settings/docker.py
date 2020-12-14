from .dev import *

# Allow all hosts, since all requests will typically come from outside the container
ALLOWED_HOSTS = ["*"]

# Redis server for channels, expected to run as a service in the docker-compose setup
# fmt: off
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
        },
    },
}
# fmt: on
