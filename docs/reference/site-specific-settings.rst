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

See :ref:`howto-change-settings`

List of settings and environment variables
==========================================

.. warning:: Environment variables and Argus settings may contain sensitive data, such
  as login credentials, secrets and passwords.
  Be mindful when setting these variables, and use appropriate safety precautions.
  For example, do not check your ``localsettings.py`` files into version control.

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

.. _site-specific-settings-additional-apps:

Settings for adding additional Django apps
------------------------------------------

.. setting:: OVERRIDING_APPS

* :setting:`OVERRIDING_APPS` is a list of dicts of additional apps added
  *before* the default list of :setting:`INSTALLED_APPS` which means that
  templates and static files found here can *override* what comes later.
  Environment variable: ``ARGUS_OVERRIDING_APPS``

.. setting:: EXTRA_APPS

* :setting:`EXTRA_APPS` is a list of dicts of additional apps added *after* the
  default list of :setting:`INSTALLED_APPS` which means that templates and
  static files found here add extra templates and static files *without*
  overriding what is already there. Environment variable: ``ARGUS_EXTRA_APPS``

Format of the app settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

Both settings are a list of dicts.

App
...

To add an app, the minimal content of the dict is::

    { "app_name": "myapp" }

"myapp" is the same string you would normally put into
:setting:`INSTALLED_APPS`.

Settings
........

You can overwrite any setting with the "settings"-key::

    {
        "settings": {
            "LOGIN_URL": "/magic/"
        }
    }

This is useful for settings that do not belong to specific apps.

You can set settings for an app too::

       {
           "app_name": "myapp",
           "settings": {
               "MYAPP_MAGIC_NUMBER": 785464279385649275692
           }
       }

Urls
....

There is an experimental way of also overriding or extending the root
``urls.py`` in ``argus.site``.

.. warning:: This format is subject to change. Do not override the urls this
   way in production just yet.

There are two possible formats:

1. Without namespace::

       {
           "app_name": "myapp",
           "urls": {
               "path": "myapp/",
               "urlpatterns_module": "myapp.urls"
           }
       }

   This is translated to::

       path("myapp/", include("myapp.urls"))

2. With namespace::

       {
           "app_name": "myapp",
           "urls": {
               "path": "myapp/",
               "urlpatterns_module": "myapp.urls",
               "namespace": "mynamespace"
           }
       }

   This is translated to::

       path("myapp/", include("myapp.urls", "mynamespace"))

This assumes that ``myapp.urls`` contains a variable named ``urlpatterns`` with
the defined urls of the app.

Context processors
..................

Optionally, one or more context processors can be added to the end of the
context processors list of the
``django.template.backends.django.DjangoTemplates`` template backend.

Format::

    {
        "app_name": "holiday_cheer",
        "context_processors": [
            "holiday_cheer.context_processors.date_context",
            "holiday_cheer.context_processors.holidays"
        ]
    }

Context processors that are not specific to an app can also be set::

    {
        "context_processors": [
            "django.template.context_processors.debug"
        ]
    }

Middleware
..........

Optionally, additional middlewares can be added to the :setting:`MIDDLEWARE`-setting.

Format::

    {
        "app_name": "holiday_cheer",
        "middleware": {
            "holiday_cheer.appended_middleware": "end",
            "holiday_cheer.prepended_middleware": "start"
        }
    }

Subformat::

    "dotted-path-to-middleware": ACTION

Adding middleware is trickier than other settings as the order matters. The
default is appending (ACTION is "end" or a random string), but it is also
possible to prepend (ACTION is "start"). A prepended middleware will be run
*before* the security- and session middlewares which might not be what you
want.

Middleware not belonging to an app can also be added::

    {
        "middleware": {
            "django.middleware.cache.GZipMiddleware": "end"
        }
    }

Database settings
-----------------

.. setting:: DATABASE_URL

* :setting:`DATABASE_URL` contains the URL and port, as well as username, password, and name
  of the database to be used by Argus.

A common value in development would be::

  DATABASE_URL=postgresql://argus_user:superSecretPassword@localhost:5432/argus_db

Incident settings
-----------------

.. setting:: INDELIBLE_INCIDENTS

* :setting:`INDELIBLE_INCIDENTS` protects incidents from being deleted. The
  default is ``True``. This can also be set via the environment variable
  ``ARGUS_INDELIBLE_INCIDENTS``.

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

Token settings
------------------

.. setting:: AUTH_TOKEN_EXPIRES_AFTER_DAYS

* :setting:`AUTH_TOKEN_EXPIRES_AFTER_DAYS`  determines how long an authentication token is valid.
    If undefined it will default to the value of 14 days.

Ticket system settings
----------------------

``TICKET_PLUGIN``, ``TICKET_ENDPOINT``, ``TICKET_AUTHENTICATION_SECRET``,
``TICKET_INFORMATION`` are all described in :ref:`ticket-systems-settings`.

Special environment settings
----------------------------

.. setting:: BANNER_MESSAGE

* :setting:`BANNER_MESSAGE` is a message displayed below the navbar in
  a banner. It can be used to communicate an important message to the users on
  all Argus pages, for example, to announce maintenance work or indicate that
  the Argus instance is running in demo mode. The default value is ``None``. If
  set it should only contain plain text, not HTML.

* Environment variable: `ARGUS_BANNER_MESSAGE`

* Note: To enable the banner, the context processor
  ``argus.htmx.context_processors.banner_message`` *must* be in the context
  processors list in the ``django.template.backends.django.DjangoTemplates``
  template backend.

Debugging settings
------------------

.. setting:: DEBUG

* :setting:`DEBUG` enables or disables debug-mode.

.. setting:: TEMPLATE_DEBUG

* :setting:`TEMPLATE_DEBUG` (optional) provides a convenient way to turn debugging on and off
  for templates. If undefined it will default to the value of :setting:`DEBUG`.

