==============================
Setting site-specific settings
==============================

There are several site-specific settings that need to somehow be set (and
**not** checked in to version control.

* SECRET_KEY
* Any API keys, for instance OIDC keys and secrets
* DEBUG. Newer Djangos don't have a oneliner to easily turn debugging on and
  off for templates, but Argus supports TEMPLATE_DEBUG for this.
* DATABASE-settings
* EMAIL-settings

ALLOWED_HOSTS is safe to check in, but it is very much deployment specific.

Variant 1: Use a separate settings.py file
==========================================

This gives you the most control, and is basically what
``argus.site.settings.dev`` and ``argus.site.settings.prod`` is. Both the extra
settings-file and ``argus`` must be in the python path of whatever needs the
settings. However, this doesn't solve the problem of how to protect secrets,
and hence is less suited for production environments.

Variant 2: Use shell environment variables
==========================================

Environment variables are limited to numbers and strings. Use ``1`` for boolean
``True``, ``0`` for boolean ``False``. Strings might need to be quoted with
double quotes, ``"``. Backspace is magic, so avoid it in passwords.

This is the 12 factor way.

Currently, the following settings/environment variables are supported:

* DEBUG
* TEMPLATE_DEBUG
* ARGUS_DATAPORTEN_SECRET, which holds the password for using dataporten for
  authentication.
* ARGUS_FRONTEND_URL, by default "http://localhost:3000", for CORS
* EMAIL_HOST, smarthost to send email through
* EMAIL_HOST_PASSWORD, password if the smarthost needs that
* EMAIL_PORT, in production by default set to 587
* SECRET_KEY, used internally by django, should be about 50 chars of ascii
  noise (but avoid backspaces!)

If you wish to set more this way, set them in a separate settings-file, like
``argus.site.settings.dev`` and ``argus.site.settings.prod`` demonstrates,
basically combining variant 1 and 2.

How to set environment variables
================================

Consult the manual for your shell for how to do this. In bash/zsh it is::

    $ export DEBUG=1

Deployment-specific systems like docker-compose, heroku, kubernetes, might
also have their own way of setting environment variables.
