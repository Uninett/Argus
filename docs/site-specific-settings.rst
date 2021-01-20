.. _site-specific-settings:

======================
Site-specific settings
======================

There are several settings that need to be defined within Argus, for example:

* ``SECRET_KEY``
* Any API keys, for instance OIDC keys and secrets
* ``DEBUG``
* ``DATABASE``-settings
* ``EMAIL``-settings

Two ways to define these site-specific settings are explained as follows.

Variant 1: Using environment variables in the shell
===================================================

Site-specific settings can be set per 12 factor, using environment variables.

Note that environment variables can only contain numbers and strings as values.
Strings have to be enclosed with double quotes, ``"a simple string"``.
Use ``1`` to represent Boolean True, ``0`` for False.

In bash/zsh you set an environment variable like this::

    $ export DEBUG=1

Deployment-specific systems like docker-compose, heroku or kubernetes might have their
own way of setting environment variables.

Variant 2: Using a ``settings.py`` file
=======================================

A settings file is a regular python file.
This allows the use more complex Python data types than environment variables.
A settings file will override any environment variables.

``argus.site.settings.dev`` and ``argus.site.settings.prod`` provide reasonable defaults
for development and production environment. You can use and/or override them by
importing them to your ``localsettings.py`` as follows::

  from argus.site.settings.prod import *

Now define variables like::

  DEBUG = True

Settings can be tested in ``localsettings.py`` and moved to the other settings files
later.
Use an expressive name for your ``settings.py`` file, such as ``prod-settings.py``.


You can combine settings files and environment variables.


List of settings and environment variables
==========================================

Django-specific settings
------------------------

* ``DJANGO_SETTINGS_MODULE`` is the environment variable to invoke the Django settings
  module, or settings file. For a development environment, reasonable defaults are
  provided in ``argus.site.settings.dev``. In production, a ``settings.py`` file should
  be created and invoked here.
* ``SECRET_KEY`` is the Django secret key for this particular Argus instance.
  It contains a minimum of 50 random characters.
  The recommended way to generate this key is calling the command::

      $ python manage.py gen_secret_key

  .. warning:: Keep the ``SECRET_KEY`` secret, as it is relevant to the
    security and integrity of your Argus instance.

Dataporten
----------

* ``ARGUS_DATAPORTEN_KEY`` holds the id/key for using dataporten for authentication.
* ``ARGUS_DATAPORTEN_SECRET`` holds the dataporten password.

Refer to the section :ref:`dataporten` for more information.

Domain settings
---------------

* ``ARGUS_COOKIE_DOMAIN`` holds the domain of the Argus instance. This is the domain
  that the cookie is set for. It is needed to log into the frontend.
* ``ARGUS_FRONTEND_URL`` is used for redirecting back to frontend after logging in
  through Feide and CORS. Must either be a subdomain of or the same as
  ``ARGUS_COOKIE_DOMAIN``.

In production, Argus requires the frontend and the backend to either be deployed on the
same domain, or the frontend to be on a subdomain of the ``ARGUS_COOKIE_DOMAIN``.
When running Argus on localhost for development and testing, ``ARGUS_COOKIE_DOMAIN`` can
be empty (and will default to localhost).

Database settings
-----------------

* ``DATABASE_URL`` contains the URL and port, as well as username, password, and name
  of the database to be used by Argus.

A common value in development would be::

  DATABASE_URL=postgresql://argus_user:superSecretPassword@localhost:5432/argus_db

Notification settings
---------------------

* ``ARGUS_SEND_NOTIFICATIONS`` allows sending or suppressing notifications.
  Default values are ``1`` in production and ``0`` otherwise.
* ``DEFAULT_FROM_EMAIL`` the email address Argus uses as sender of email notifications.
* ``EMAIL_HOST`` contains the smarthost (domain name) to send email through.
* ``EMAIL_HOST_USER`` (optional) username for email host (if required).
* ``EMAIL_HOST_PASSWORD`` (optional) password for the email host (if required).
* ``EMAIL_PORT`` (optional) email port. Defaults to 587 in production.

In the settings file, there are also settings for which notification plugins to
use:

* ``DEFAULT_EMAIL_MEDIA`` is enabled by default and uses Django's email backend. There
  are multiple email backends available that Argus' plugin supports. It is recommended
  to simply switch out the email backend instead of replacing this plugin.
* ``DEFAULT_SMS_MEDIA`` is disabled by default, since there is no standardized
  way of sending SMS messages. The only supported media at the moment is
  Uninett's internal email-to-SMS gateway.

Enabling the email-to-SMS gateway
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Argus supports sending SMS text messages via an email-to-SMS gateway, provided
that this gateway conforms to the following interface:

The gateway receives email sent to a specific address. The email must contain
the recipient's phone number in the subject line. The body of the email will be
sent as a text message to this number.

Argus comes with an SMS notification class that supports this kind of
interface.  To enable it:

* Set ``DEFAULT_SMS_MEDIA="argus.notificationprofile.media.sms_as_email.SMSNotification"``.
* Set ``SMS_GATEWAY_ADDRESS`` to the email address of the gateway.



Realtime updates
----------------

The Argus API can notify the frontend about changes in the list of open
incidents in realtime, using a websocket (implemented using Django
Channels). The realtime interface requires access to a Redis server for message
passing.

By default, Argus will look for a Redis server on ``localhost:6379``. To use a
different server, set the ``ARGUS_REDIS_SERVER`` environment variable, e.g::

  ARGUS_REDIS_SERVER=my-redis-server.example.org:6379


Debugging settings
------------------

* ``DEBUG`` enables or disables debug-mode.
* ``TEMPLATE_DEBUG`` (optional) provides a convenient way to turn debugging on and off
  for templates. If undefined, it will default to the value of ``DEBUG``.

.. warning:: Environment variables and Argus settings may contain sensitive data, such
  as login credentials, secrets and passwords.
  Be mindful when setting these variables, and use appropriate safety precautions.
  For example, do not check your ``localsettings.py`` files into version control.
