# Gunicorn configuration file
# https://gunicorn.org/configure/#configuration-file
# https://gunicorn.org/reference/settings/

LOWEST_LOGLEVEL = "INFO"

ROOT_LOGGER = {
    "level": LOWEST_LOGLEVEL,
    "handlers": ["console"],
}

# logging

accesslog = "-"
errorlog = "-"

access_log_format = '"%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"  # gunicorn error log, hide noise

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plaintext": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plaintext",
        },
    },
    # Gunicorn weirdness, dict config won't work without this
    "root": ROOT_LOGGER,
    "loggers": {
        "": ROOT_LOGGER,
        "gunicorn.error": {
            "level": "INFO",
            "handlers": [
                "console",
            ],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": [
                "console",
            ],
            "propagate": False,
        },
    },
}
