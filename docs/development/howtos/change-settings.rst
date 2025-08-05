.. _howto-change-settings:

====================================
How to change site-specific settings
====================================

Two ways to define these site-specific settings follow.

The management command ``print_settings`` (which depends on the app
``django-extensions``, a ``dev``-dependency installable via ``pip
install argus-server[dev]``) will print out the complete
settings that will be used.


Variant 1: Using environment variables in the shell
===================================================

A subset of settings can be set per 12 factor, using environment variables.

Note that environment variables can only contain numbers and strings as values.
Strings have to be enclosed with double quotes, ``"a simple string"``.
Use ``1`` to represent Boolean True, ``0`` for False.

In bash/zsh you set an environment variable like this::

    $ export DEBUG=1

Deployment-specific systems like docker-compose, heroku or kubernetes might have their
own way of setting environment variables.

Variant 2: Using a ``settings.py`` file
=======================================

A settings file is a regular importable Python file. The filename MUST start
with a letter, MUST only contain letters, numbers or underscores ("_"), and
MUST end with ".py".

This allows the use of more complex Python data types than environment variables.
A settings file may override anything set via environment variable.

``argus.site.settings.dev`` has reasonable defaults for development while
``argus.site.settings.prod`` is a good starting point for production.

.. note:: The development settings file assumes that the optional development
   dependencies are installed. You can get them via ``pip install argus-server[dev]``.

Development
~~~~~~~~~~~

Do this in your working directory, which could be the checked out `argus-server
<https://github.com/Uninett/Argus>`_ repo.

This assumes that you have a local settings file (we recommend calling it
"localsettings.py" since that is hidden by .gitignore) as a sibling of
``src/``.

At the top of this local settings file you should have::

   from argus.site.settings.dev import *

There, now you can alter anything.

If you don't want to use any of the development dependencies you can import
from ``argus.htmx.settings`` instead.

Settings can be tested in ``localsettings.py`` and moved to other settings files
later.

Production
~~~~~~~~~~

Copy the contents of ``argus.site.settings.prod`` to your own settings-file.
It does not depend on any development dependencies. It will also turn on some
extra nagging for settings that MUST be set for production.

For production you MUST set :setting::`ALLOWED_HOSTS`, note how it's
commented out in ``argus.site.settings.prod``.

Use an expressive name for your ``settings.py`` file, such as
``production_settings.py``.

You can combine settings files and environment variables.
