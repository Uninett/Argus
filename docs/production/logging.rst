=====================
Logging in production
=====================

Structured logging with JSON
============================

For log analysis it is frequently useful to have the logs in a structured
format.

By installing ``python-json-logger`` (for instance via ``pip install
python-json-logger`` or ``pip install ".[jsonlogging]"``) and setting up
a logging formatter like this:

::

    "formatters": {
        ..
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "asctime,levelname,name,message",
            "style": ",",
        },
        ..
    },
    "handlers": {
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },

... the logs produced by argus will be in JSON format.

See `Python logging LogRecord attributes
<https://docs.python.org/3/library/logging.html#logrecord-attributes>`_ for
other default keywords useful to put in the "format"-line. "message" is
a human-chosen plaintext explicitly written in the code and should always be
included.
