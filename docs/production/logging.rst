=====================
Logging in production
=====================

In production there are at least three different configurable sources of logs:

1. The webserver, load balancer or proxy: First line of defense.
2. The WSGI or ASGI server that talks WSGI or ASGI with Argus. Translates
   between 1 and 3.
3. Argus itself.

Both point 1 and 2 will have access logs, unless you turn it off. Both 1 and
2 will have error logs for that layer only. Only layer 3 will produce error
logs for errors in Argus itself.

For development, Django (and thus Argus) ships with the development command
"runserver", which combines both 1 and 2. But in production, it is better to
have layer 1 and 2 separate, and layer 2 should never be just "runserver".

Layers 1 and 2 are outside Argus' control, so we cannot ship a logging
configuration for them. This page documents what we recommend.

Structured logging with JSON
============================

For log analysis it is frequently useful to have the logs in a structured
format.

By installing ``python-json-logger`` (for instance via ``pip install
python-json-logger`` or ``pip install ".[jsonlogging]"``) and setting up
a logging formatter like this. Elided lines are marked with ``..``:

::

    ..
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "asctime,levelname,name,message",
            "style": ",",
        },
    },
    "handlers": {
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        ..
        "argus": {
            ..
            "handlers": ["json"],
            "propagate": False,
        },
        ..
    },
    ..

… the logs produced by Argus will be in JSON format.

See `Python logging LogRecord attributes
<https://docs.python.org/3/library/logging.html#logrecord-attributes>`_ for
other default keywords useful to put in the "format"-line. "message" is
a human-chosen plaintext explicitly written in the code and should always be
included.

Gunicorn as layer 2
===================

Use a configuration file, and in the configuration, set up logging for gunicorn
itself. If both gunicorn and Argus are set to use ``logging.StreamHandler``
then the gunicorn logs and Argus logs end up the same place. Gunicorn uses
``logging.StreamHandler`` by default.

See :download:`example gunicorn configuration with plaintext logs
<gunicorn.conf.py>` or :download:`example gunicorn configuration with JSON logs
<gunicorn-json.conf.py>`.

.. Note::
   ``logconfig_dict`` overrides ``accesslog``, ``errorlog`` and
   ``loglevel``, so don't mix them. ``access_log_format`` is always honored.

.. Warning::
   Argus' logging configuration is applied after gunicorn's, in the same
   process. If it sets ``disable_existing_loggers`` to ``True`` (the default
   if the key is left out), gunicorn's own loggers (``gunicorn.error`` and
   ``gunicorn.access``) are disabled, and the access log silently disappears.
   Set it to ``False``, or list both gunicorn loggers in Argus' configuration.

Troubleshooting
===============

.. _duplicate_logs:

The same message is logged multiple times
-----------------------------------------

This happens if a handler is set on a sublogger in addition to the root
logger without setting ``propagate`` to ``False`` in the sublogger.

With a dictionary based config, elided lines are marked with ``..``. If you have::

    {
        ..
        "loggers": {
            "": {
                "level": "DEBUG",
                "handlers": ["json"],
            },
            "argus": {
                "level": "DEBUG",
                "handlers": ["json"],
            },
            ..
        }
    }

Change it to::

    {
        ..
        "loggers": {
            "": {
                "level": "DEBUG",
                "handlers": ["json"],
            },
            "argus": {
                "level": "DEBUG",
                "handlers": ["json"],
                "propagate": False,
            },
            ..
        }
    }


The same message is logged multiple times in different formats
--------------------------------------------------------------

It's caused by having multiple handlers sending to the same place.

It's one of:

1. Multiple handlers, and the subloggers do not have ``propagate`` set to
   ``False``, see :ref:`duplicate_logs`.
2. Multiple entries in the handlers-list that send to the same place. Example
   with a dictionary based config, elided lines are marked with ``..``. If you have:

   ::

       {
           ..
           "handlers": {
               "console": {
                   "class": "mycode.myhandler",
                   "formatter": "console",
               },
               "json": {
                   "class": "mycode.myhandler",
                   "formatter": "json",
               },
               ..
           },
           "loggers": {
           ..
               "argus": {
                   "level": "DEBUG",
                   "handlers": ["json", "console"],
               },
               ..
           }
       }


   … this will lead to everything logged under argus being sent twice to the
   same place, in two different formats.

Not enough detail
-----------------

If you suspect that 3rd party libraries have interesting things to log, set
``disable_existing_loggers`` to ``False``. They won't follow the format set for
Argus by default so you might wish to add them to the list of loggers and
choose a level and formatter for them.

Argus itself has an additional log level, ``TRACE``, numeric value ``5``, for
even more noise than ``DEBUG``. Some 3rd party libraries use this level too.
We don't recommend ``TRACE`` in production.
