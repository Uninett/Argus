# fmt: off

# Copied from django 3.0.x django.utils.log.DEFAULT_LOGGING
DEFAULT = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

DEV = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            # exact format is not important, this is the minimum information
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        },
        "django.server": DEFAULT["formatters"]["django.server"],
    },
    "handlers": {
        "null": {
            "class": "logging.NullHandler",

        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "django.server": DEFAULT["handlers"]["django.server"],
    },
    "loggers": {
        # root logger
        "": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
        "django.db.backends": {
            "handlers": ["null"],
            "level": "NOTSET",
            "propagate": False,
        },
        "django.utils.autoreload": {
            "handlers": ["null"],
            "level": "NOTSET",
            "propagate": False,
        },
        #"django.server": DEFAULT["loggers"]["django.server"],
    }
}
# fmt: on
