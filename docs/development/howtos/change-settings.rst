====================================
How to change site-specific settings
====================================

Two ways to define these site-specific settings follow.

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

A settings file is a regular Python file.
This allows the use of more complex Python data types than environment variables.
A settings file will override any environment variables.

``argus.site.settings.dev`` and ``argus.site.settings.prod`` provide reasonable defaults
for development and production environments. You can use and/or override them by
importing them to your ``localsettings.py`` as follows::

  from argus.site.settings.prod import *

Now define variables like::

  DEBUG = True

Settings can be tested in ``localsettings.py`` and moved to the other settings files
later.
Use an expressive name for your ``settings.py`` file, such as ``prod-settings.py``.

You can combine settings files and environment variables.
