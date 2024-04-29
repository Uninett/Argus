===================
argus-HTMx-frontend
===================

Experimental frontend for `argus-server`_ as a django app.

Will possibly cease to exist as a separate app if the experiment is deemed
successful.

See `argus-server`_ for more abour argus.

Imports `django-htmx`_. See the `documentation for django-htmx`_
for details.

How to play
===========

Install
-------

To make sure you do not accidentally work on an old argus-server, do the following:

1. Use/make a venv, for instance: create a new one with ``python -m venv argus-htmx``
2. Check out argus-server code
3. Install argus-server dynamically into the venv: ``pip install -e .``
4. Check out this repo
5. Install this app dynamically into the venv: ``pip install -e .``

It is now safe to remove argus-server from the venv if you feel like it.

Configure
---------

Do this in your workdir, which could be the checked out `argus-server`_ repo.

Django-style
~~~~~~~~~~~~

In your local settings that star-imports from an `argus-server`_ settings file::

    INSTALLED_APPS += [
        "django_htmx",
        "argus_htmx",
    ]
    ROOT_URLCONF = "urls.py"
    MIDDLEWARE += ["django_htmx.middleware.HtmxMiddleware"]

Next to ``localsettings.py`` create an ``urls.py`` containing::

   from argus.site.urls import urlpatterns

   urlpatterns += [
       path("", include("argus_htmx.urls")
   ]

With EXTRA_APPS
~~~~~~~~~~~~~~~

In your environment variables::

    ARGUS_EXTRA_APPS = '[{"app_name": "django_htmx"},{"app_name": "argus_htmx","urls": {"path": "", "urlpatterns_module": "argus_htmx.urls"}}]'

In your local settings that star-imports from an `argus-server`_ settings file::

    MIDDLEWARE += ["django_htmx.middleware.HtmxMiddleware"]

.. _django-htmx: https://github.com/adamchainz/django-htmx
.. _argus-server: https://github.com/Uninett/Argus
.. _documentation for django-htmx: https://django-htmx.readthedocs.io/en/latest/
