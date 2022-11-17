.. _site-specific-settings:

======================
Site-specific settings
======================

There are several settings that need to be defined within Argus, for example:

* :setting:`SECRET_KEY`
* Any API keys, for instance OIDC keys and secrets
* :setting:`DEBUG`
* :setting:`DATABASE_URL`
* :setting:`DEFAULT_FROM_EMAIL`

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
This allows the use of more complex Python data types than environment variables.
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

.. setting:: DJANGO_SETTINGS_MODULE

* :setting:`DJANGO_SETTINGS_MODULE` is the environment variable to invoke the Django settings
  module, or settings file. For a development environment, reasonable defaults are
  provided in ``argus.site.settings.dev``. In production, a ``settings.py`` file should
  be created and invoked here.

.. setting:: SECRET_KEY

* :setting:`SECRET_KEY` is the Django secret key for this particular Argus instance.
  It contains a minimum of 50 random characters.
  The recommended way to generate this key is calling the command::

      $ python manage.py gen_secret_key

  .. warning:: Keep the :setting:`SECRET_KEY` secret, as it is relevant to the
    security and integrity of your Argus instance.

Dataporten
----------

.. setting:: ARGUS_DATAPORTEN_KEY

* :setting:`ARGUS_DATAPORTEN_KEY` holds the id/key for using dataporten for authentication.

.. setting:: ARGUS_DATAPORTEN_SECRET

* :setting:`ARGUS_DATAPORTEN_SECRET` holds the dataporten password.

Refer to the section :ref:`dataporten` for more information.

Domain settings
---------------

.. setting:: ARGUS_COOKIE_DOMAIN

* :setting:`ARGUS_COOKIE_DOMAIN` holds the domain of the Argus instance. This is the domain
  that the cookie is set for. It is needed to log into the frontend.

.. setting:: ARGUS_FRONTEND_URL

* :setting:`ARGUS_FRONTEND_URL` is used for redirecting back to frontend after logging in
  through Feide and CORS. Must either be a subdomain of or the same as
  :setting:`ARGUS_COOKIE_DOMAIN`.

In production, Argus requires the frontend and the backend to either be deployed on the
same domain, or the frontend to be on a subdomain of the :setting:`ARGUS_COOKIE_DOMAIN`.
When running Argus on localhost for development and testing, :setting:`ARGUS_COOKIE_DOMAIN` can
be empty (and will default to localhost).

Database settings
-----------------

.. setting:: DATABASE_URL

* :setting:`DATABASE_URL` contains the URL and port, as well as username, password, and name
  of the database to be used by Argus.

A common value in development would be::

  DATABASE_URL=postgresql://argus_user:superSecretPassword@localhost:5432/argus_db

Notification settings
---------------------

.. setting:: ARGUS_SEND_NOTIFICATIONS

* :setting:`ARGUS_SEND_NOTIFICATIONS` allows sending or suppressing notifications.
  Default values are ``1`` in production and ``0`` otherwise.

.. setting:: DEFAULT_FROM_EMAIL

* :setting:`DEFAULT_FROM_EMAIL` the email address Argus uses as sender of email notifications.

.. setting:: EMAIL_HOST

* :setting:`EMAIL_HOST` contains the smarthost (domain name) to send email through.

.. setting:: EMAIL_HOST_USER

* :setting:`EMAIL_HOST_USER` (optional) username for email host (if required).

.. setting:: EMAIL_HOST_PASSWORD

* :setting:`EMAIL_HOST_PASSWORD` (optional) password for the email host (if required).

.. setting:: EMAIL_PORT

* :setting:`EMAIL_PORT` (optional) email port. Defaults to 587 in production.

.. setting:: MEDIA_PLUGINS

In the settings file there is also the variable :setting:`MEDIA_PLUGINS`, which holds the paths
to the media classes and determines which notification plugins are available to send notifications by.

Email is enabled by default and uses Django's email backend. There are multiple email
backends available that Argus' plugin supports. It is recommended to simply switch out
the email backend instead of replacing this plugin.

SMS is disabled by default, since there is no standardized way of sending SMS messages.
The only supported way at the moment is Sikt's internal email-to-SMS gateway.

Enabling the email-to-SMS gateway
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. setting:: SMS_GATEWAY_ADDRESS

Argus supports sending SMS text messages via an email-to-SMS gateway, provided
that this gateway conforms to the following interface:

The gateway receives email sent to a specific address. The email must contain
the recipient's phone number in the subject line. The body of the email will be
sent as a text message to this number.

Argus comes with an SMS notification class that supports this kind of
interface.  To enable it:

* Add ``"argus.notificationprofile.media.sms_as_email.SMSNotification"`` to :setting:`MEDIA_PLUGINS`.
* Set :setting:`SMS_GATEWAY_ADDRESS` to the email address of the gateway.

Using the fallback notification filter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. setting:: ARGUS_FALLBACK_FILTER

The setting  :setting:`ARGUS_FALLBACK_FILTER` is a dict, by default undefined. You can
set this to ensure a systemwide fallback filter for everyone:

Examples:

Do not send notifications on ACKED events::

    ARGUS_FALLBACK_FILTER = {"acked": False}

Ignore low priority incidents by default::

    ARGUS_FALLBACK_FILTER = {"maxlevel": 3}

Do both::

    ARGUS_FALLBACK_FILTER = {"acked": False, "maxlevel": 3}

Realtime updates
----------------

.. setting:: ARGUS_REDIS_SERVER

The Argus API can notify the frontend about changes in the list of open
incidents in realtime using a websocket (implemented using Django
Channels). The realtime interface requires access to a Redis server for message
passing.

By default, Argus will look for a Redis server on ``localhost:6379``. To use a
different server, set the :setting:`ARGUS_REDIS_SERVER` environment variable, e.g::

  ARGUS_REDIS_SERVER=my-redis-server.example.org:6379

Token settings
------------------

.. setting:: AUTH_TOKEN_EXPIRES_AFTER_DAYS

* :setting:`AUTH_TOKEN_EXPIRES_AFTER_DAYS`  determines how long an authentication token is valid.
    If undefined it will default to the value of 14 days.

Ticket system settings
----------------------

``TICKET_PLUGIN``, ``TICKET_ENDPOINT``, ``TICKET_AUTHENTICATION_SECRET``,
``TICKET_INFORMATION`` are all described in :ref:`ticket-systems-settings`.

Debugging settings
------------------

.. setting:: DEBUG

* :setting:`DEBUG` enables or disables debug-mode.

.. setting:: TEMPLATE_DEBUG

* :setting:`TEMPLATE_DEBUG` (optional) provides a convenient way to turn debugging on and off
  for templates. If undefined it will default to the value of :setting:`DEBUG`.

Other settings
--------------

Normally, you shouldn't need to ever change these. If you do need to touch
them, do it via a new settings file containing overrides.

.. setting:: ARGUS_TOKEN_COOKIE_NAME

* :setting:`ARGUS_TOKEN_COOKIE_NAME` is to control the name of the cookie that
  contains a copy of the authentication token which is used when logging in via
  the frontend. The default is ``token``, and you can change this to
  something else if something you cannot change in the same system also creates
  a cookie with the name ``token``.

.. warning:: Environment variables and Argus settings may contain sensitive data, such
  as login credentials, secrets and passwords.
  Be mindful when setting these variables, and use appropriate safety precautions.
  For example, do not check your ``localsettings.py`` files into version control.
