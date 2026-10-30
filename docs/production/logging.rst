=====================
Logging in production
=====================

In production there are at least three different configurable sources of logs:

1. The webserver, load balancer or proxy: First line of defense.
2. The WSGI or ASGI server that talks WSGI or ASGI with Argus. Translates
   between 1 and 3.
3. Argus itself

Both point 1 and 2 will have access logs, unless you turn it off. Both 1 and
2 will have error logs for that layer only. Only layer 3 will produce error
logs for errors in Argus itself.

For development, Django (and thus Argus) ships with the development command
"runserver", which combines both 1 and 2. But in production, it is better to
have layer 1 and 2 separate, and layer 2 should never be just "runserver".

Because both layer 1 and 2 are outside of the control of the source code of
Argus we cannot ship a working logging configuration for those layers together
with the code, but we can document what's wise.

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

Gunicorn as layer 2
===================

Use a configuration file, and in the configuration, set up logging for gunicorn
itself. If both gunicorn and Argus is set to use ``logging.StreamHandler`` then
the gunicorn logs and Argus logs should end up on standard out.

See :download:`example gunicorn configuration <gunicorn.conf.py>` or :download:`example
gunicorn configuration with JSON logs <gunicorn-json.conf.py>`.

Troubleshooting
===============

.. _duplicate_logs:

The some message is logged multiple times
-----------------------------------------

This happens if a handler is set on a sublogger in addition to the root
logger without setting ``propagate`` to ``False`` in the sublogger.

With a dictionary based config, elided lines marked with `..`. If you have::

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


The some message is logged multiple times in different formats
--------------------------------------------------------------

It's caused by having multiple handlers sending to the same place.

It's one of:

1. Multiple handlers, and the subloggers do not have ``propagate`` set to
   False, see :ref:`duplicate_logs`.
2. Multiple entries in the handlers-list that send to the same place. Example
   with a dictionary based config, elided lines marked with `..`. If you have:

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


    .. this will lead to everything logged under argus being sent twice to the
    same place.
