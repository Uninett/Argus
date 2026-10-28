# Gunicorn configuration file
# https://gunicorn.org/configure/#configuration-file
# https://gunicorn.org/reference/settings/

from pythonjsonlogger.json import JsonFormatter

LOWEST_LOGLEVEL = "INFO"

ROOT_LOGGER = {
    "level": LOWEST_LOGLEVEL,
    "handlers": ["json"],
}


class AccessJsonFormatter(JsonFormatter):
    def format(self, record):
        # to alter what is copied to JSON: dump vars(record) and record.args
        record.access = {
            "http": record.args["r"],
            "remote_address": record.args["h"],
            "user_name": record.args["u"],
            "date": record.args["t"],
            "status": record.args["s"],
            "method": record.args["m"],
            "url_path": record.args["U"],
            "query_string": record.args["q"],
            "protocol": record.args["H"],
            "response_length": record.args["B"],
            "referer": record.args["f"],
            "user_agent": record.args["a"],
            "request_time_seconds": record.args["L"],
        }
        return super().format(record)


# logging

accesslog = "-"
errorlog = "-"

access_log_format = '"%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"  # gunicorn error log, hide noise

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "reserved_attrs": ["msg", "args"],
        },
        "json_access_log": {
            "()": AccessJsonFormatter,
            "reserved_attrs": ["msg", "args"],
        },
    },
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "json_access_log": {
            "class": "logging.StreamHandler",
            "formatter": "json_access_log",
        },
    },
    # Gunicorn weirdness, dict config won't work without this
    "root": ROOT_LOGGER,
    "loggers": {
        "": ROOT_LOGGER,
        "gunicorn.error": {
            "level": "INFO",
            "handlers": [
                "json",
            ],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": [
                "json_access_log",
            ],
            "propagate": False,
        },
    },
}
