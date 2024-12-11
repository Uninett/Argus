==========================================================
How to toggle the usage of django-debug-toolbar on and off
==========================================================

Shipping to production with django-debug-toolbar turned on is bad news. Instead
of manually altering settings, you can use the extra-apps machinery to easily
control if django-debug-toolbar is configured or not.

Make sure it is installed
=========================

You need to have django-debug-toolbar installed for this, it's part of the dev-dependencies so you can get ot through any of::

        pip install django-debug-toolbar

or::

        pip install argus-server[dev]

or::

        pip install -r requirements/dev.txt

Set up extra-apps with django-debug-toolbar
===========================================

Create a JSON-file, let's call it ``debug-toolbar.json``,  with the
following contents::

        [
          {
            "app_name": "debug_toolbar",
            "urls": {
              "path": "__debug__/",
              "urlpatterns_module": "debug_toolbar.urls"
            },
            "middleware": {
              "debug_toolbar.middleware.DebugToolbarMiddleware": "end"
            }
          }
        ]

Toggle django-debug-toolbar on
==============================

This assumes a bash-compatible shell.

Set the environment variable ``EXTRA_APPS``::

        export EXTRA_APPS=`cat debug-toolbar.json`

Reload site.

Toggle django-debug-toolbar off
===============================

This assumes a bash-compatible shell.

Unset the environment variable ``EXTRA_APPS``::

        unset EXTRA_APPS

Reload site.
