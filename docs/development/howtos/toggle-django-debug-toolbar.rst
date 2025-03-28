==========================================================
How to toggle the usage of django-debug-toolbar on and off
==========================================================

Shipping to production with ``django-debug-toolbar`` turned on is bad news.
Instead of manually altering settings, you can use the extra-apps machinery to
easily control if ``django-debug-toolbar`` is configured or not.

Set up
======

Make sure it is installed
-------------------------

You need to have ``django-debug-toolbar`` installed for this, it's part of the
dev-dependencies so you can get it through any of::

        pip install django-debug-toolbar

or::

        pip install argus-server[dev]

or::

        pip install -r requirements/dev.txt

Set up extra-apps with django-debug-toolbar
-------------------------------------------

Create a JSON-file, let's call it ``debug-toolbar.json``,  with the
following contents:

.. code-block:: json

        [
          {
            "app_name": "debug_toolbar",
            "middleware": {
              "debug_toolbar.middleware.DebugToolbarMiddleware": "end"
            },
            "settings": {
              "DEBUG_TOOLBAR_CONFIG": {
                "ROOT_TAG_EXTRA_ATTRS": "hx-preserve"
              }
            },
            "urls": {
              "path": "__debug__/",
              "urlpatterns_module": "debug_toolbar.urls"
            }
          }
        ]

If you want to add settings for more apps you should probably call the file
something else.

If you haven't already set INTERNAL_IPS anywhere you can add a line
``INTERNAL_IPS = ["127.0.0.1"],`` in the settings-block, just above and as
a sibling to ``DEBUG_TOOLBAR_CONFIG``. When developing we do recommend that
INTERNAL_IPS is set even when not using ``django-debug-toolbar`` though.

(In production, it is best that ``INTERNAL_IPS`` is an empty list, for security
reasons.)

For ``django-debug-toolbar`` to work, the ip you visit the site from must be in
:setting:``INTERNAL_IPS``, and ``DEBUG`` must be ``True``. Unless you have
hardcoded ``DEBUG`` in a settings-file somewhere you can control it via an
environment variable.

Activate the django-debug-toolbar config via the environment
------------------------------------------------------------

This assumes a bash-compatible shell.

Set the environment variable ``ARGUS_EXTRA_APPS``::

        export ARGUS_EXTRA_APPS=`cat debug-toolbar.json`

Reload site.

Unless you have hardcoded the ``DEBUG``-setting anywhere, you can now toggle
``django-debug-toolbar`` on and off via the ``DEBUG`` environment variable.

Deactivate the django-debug-toolbar config via the environment
--------------------------------------------------------------

This assumes a bash-compatible shell.

Either unset the environment variable ``ARGUS_EXTRA_APPS``::

        unset ARGUS_EXTRA_APPS

Or set it to an empty list::

        export ARGUS_EXTRA_APPS="[]"

Reload site.

Toggle
======

Given that ``DEBUG`` is set to ``True`` somewhere you could activate and
deactivate the config as detailed previously, but it is probably more elegant
to toggle ``DEBUG``.

Toggle an activated django-debug-toolbar on
-------------------------------------------

This assumes a bash-compatible shell.

Set the environment variable ``DEBUG``::

        export DEBUG=1

Reload site.

Toggle an activated django-debug-toolbar off
--------------------------------------------

This assumes a bash-compatible shell.

Set the environment variable ``DEBUG``::

        export DEBUG=0

You could just unset it but explicit is very much better than implicit in this
case.

Reload site.
