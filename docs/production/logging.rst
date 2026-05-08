=====================
Logging in production
=====================

Logging a deployment-specific environment
=========================================

Utilizing the setting :setting:`ENVIRONMENT` and either the logging filter
``argus.logging.filters.EnvironmentFilter`` or the formatter
``argus.logging.formatters.EnvironmentFormatter`` it is possible to add
whatever is set in ``ENVIRONMENT`` to every line logged.

``ENVIRONMENT`` can be set via the environment variable ``ARGUS_ENVIRONMENT``.

Set it to for instance a hostname or ip address or pod name on deployment, to
make it easy to filter out which logs come from which deployment if all logs
end up at the same place.

Configure the filter, for instance via the dict method, like so::

    {
        ..
        "filters": {
            ..
            "environment": ["argus.logging.filters.EnvironmentFilter"],
            ..
        },
        ..
    }

Configure the formatter, for instance via the dict method, like so::

    {
        ..
        "formatters": {
            ..
            "environment": {
                "()": "argus.logging.formatters.EnvironmentFormatter",
                "format": "{environment} {levelname} {message}",
                "style": "{",
            },
            ..
        },
        ..
    }

Pick one of the above.

Structured logging with JSON
============================

By installing ``python-json-logger`` (for instance via ``pip install
python-json-logger`` or ``pip install ".[jsonlogging]"`` and setting up logging formatters like this:

::

    "formatters": {
        ..
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "asctime,name,funcName,levelname,message",
            "style": ",",
        },
        ..
    },

With ``python-json-logger`` installed you can also use the formatter
``argus.logging.formatters.JSONEnvironmentFormatter``.
