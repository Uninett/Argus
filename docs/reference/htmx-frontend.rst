.. _htmx-frontend:

=============
HTMx Frontend
=============

The new frontend is old-new school and uses HTMx to boost HTML pages. See the
`Github repo of argus-htmx-frontend <https://github.com/uninett/argus-htmx-frontend>`_

It has its own specific settings and currently depends on an app.

It is not needed if running headless.

It uses Tailwind CSS and daisyUI for looks and layout.

* Tailwind CSS: A utility-first CSS framework for rapidly building custom user interfaces.
* daisyUI: A component library for Tailwind CSS that provides a set of ready-to-use components as well as color themes.


Setup
=====

The app is included in the argus-server codebase, but it is optional to use.

Install Python dependencies
---------------------------

Install the dependencies::

    pip install argus-server[htmx]

(The generated requirements-files include the dependencies already.)

Install and build Tailwind CSS and daisyUI
------------------------------------------

If you want to be able to customize the frontend in any way, including changing
or adding themes, you need to install the support for Tailwind CSS and daisyUI.
They are not Python packages so it cannot be streamlined much.

Recommended but open for tweaks and adaptations steps:

Install
~~~~~~~

1. Get Tailwind standalone CLI bundled with daisyUI from
   https://github.com/dobicinaitis/tailwind-cli-extra

   Most Linux distributions::

        $ curl -sL https://github.com/dobicinaitis/tailwind-cli-extra/releases/latest/download/tailwindcss-extra-linux-x64 -o /tmp/tailwindcss
        $ chmod +x /tmp/tailwindcss

   For other OSes see
   https://github.com/dobicinaitis/tailwind-cli-extra/releases/latest/ and
   update the bit after ``download/`` accordingly.

   Optionally you can compile tailwind+daisyUI standalone cli bundle yourself as described here:
   https://github.com/tailwindlabs/tailwindcss/discussions/12294#discussioncomment-8268378.
2. (Linux/OsX) Move the tailwindcss file to your $PATH, for instance to ``~/bin/`` or ``.local/bin``.

Build
~~~~~

1. Go to the repo directory (parent of ``src/``)
2. Build main stylesheet file using ``tailwindcss`` executable from step 1 and
   pointing to the included config file:

   Manually::

        tailwindcss -c src/argus/htmx/tailwindtheme/tailwind.config.js -i src/argus/htmx/tailwindtheme/styles.css --output src/argus/htmx/static/styles.css

   Running with the ``--watch`` flag for automatic update on change seems
   error-prone so we've made it very easy to run the command, with ``make`` or ``tox``::

        make tailwind
        tox -e tailwind

   Either will rebuild the styles for you.

Configure
---------

If *all the settings you need to change* can be set via environment variables,
use ``argus.htmx.settings`` as your settings-file. Otherwise, read on.

Do this in your workdir, which could be the checked out `argus-server
<https://github.com/Uninett/Argus>`_ repo.

This assumes that you have a local settings file (we recommend calling it
"localsettings.py" since that is hidden by .gitignore) as a sibling of
``src/``.

At the top of this local settings file, copy the contents of
``argus.htmx.settings``. This will base the settings-file on
``argus.site.settings.backend`` and automatically use
``argus.site.utils.update_settings`` with
``argus.htmx.appconfig.APP_SETTINGS`` to set/overwrite some settings and
mutate others. Note the usage of ``globals()``; due to this, inheriting from
``argus.htmx.settings`` will probably not work as expected.

Example, top of settings-file for production::

   from argus.site.settings.backend import *
   from argus.site.utils import update_settings
   from argus.htmx.appconfig import APP_SETTINGS

   update_settings(globals(), APP_SETTINGS)

   ROOT_URLCONF = "argus.htmx.root_urls"

While developing you will probably prefer to swap out
``argus.site.settings.backend`` with ``argus.site.settings.dev``, as the former
is almost production-ready while the latter is tuned for development and
depends on the optional dependencies you can install via ``pip install
argus-server[dev]``.

Example, top of settings-file for development::

   from argus.site.settings.dev import *
   from argus.site.utils import update_settings
   from argus.htmx.appconfig import APP_SETTINGS

   update_settings(globals(), APP_SETTINGS)

   ROOT_URLCONF = "argus.htmx.root_urls"

The ``argus.site.utils.update_settings`` function will add or change the settings

* INSTALLED_APPS
* LOGIN_REDIRECT_URL
* LOGIN_URL
* LOGOUT_REDIRECT_URL
* LOGOUT_URL
* MIDDLEWARE
* PUBLIC_URLS
* ROOT_URLCONF
* TEMPLATES

See ``argus.htmx.appconfig._app_settings`` for what is being set.

The management command ``print_settings`` (which depends on the app
``django-extensions``, a ``dev``-dependency) will print out the complete
settings used.

Note especially that :setting:`ROOT_URLCONF` is set to
``argus.htmx.root_urls``. If you prefer to make your own root ``urls.py``, the
frontend-specific urls can be imported from ``argus.htmx.htmx_urls``.

Settings
========

Domain settings
---------------

.. setting:: ARGUS_FRONTEND_URL

* :setting:`ARGUS_FRONTEND_URL` is used for building permalinks to point back
  to incidents in the dashboard, or whenever else an absolute url is needed.

The setting must point to the publicly visible domain where the frontend is
running. This might be different from where the backend is running.

Depending on how Argus is deployed this is the only surefire way to get hold
of the externally visible hostname in the code in all cases.

OAuth2
------

.. setting:: ARGUS_<backend>_KEY

* :setting:`ARGUS_<backend>_KEY` holds the id/key for using a specific OAuth2
  backend for authentication.

.. setting:: ARGUS_<backend>_SECRET

* :setting:`ARGUS_<backend>_SECRET` holds the password for using a specific
  OAuth2 backend.

Furthermore, visiting ``/oidc/login/<backend>/`` when an Oaouth2 backend is set
up and installed will trigger a login via that backend.

See the :ref:`Authentication reference <authentication-reference>` and the
:ref:`OAuth2 howto <howto-federated-logins>` for the meaning of ``<backend>``.

OpenID Connect
--------------

Use the Python social auth backend
``social_core.backends.open_id_connect.OpenIdConnectAuth``, see
`PSA: OIDC (OpenID Connect) <https://python-social-auth.readthedocs.io/en/latest/backends/oidc.html>`_

It is only possible to connect to one OIDC provider at a time without subclassing.

If you want to use email-addresses as usernames, set
:setting:`SOCIAL_AUTH_OIDC_USERNAME_KEY` to ``"email"``. If you don't do this,
what username you will end up with is decided by the OIDC provider in question.
It could be a UUID or some other unique generated string that will not make
sense to your end-users.

You can look inside the JWT (in the model ``UserSocialAuth``, field
``extra_data``, key ``id_token``) for a different suitable value to use for
a username.

Optional authentication backend settings
----------------------------------------

RemoteUserBackend
~~~~~~~~~~~~~~~~~

If using ``django.contrib.auth.backends.RemoteUserBackend`` (which depends on
the middleware ``django.contrib.auth.middleware.RemoteUserMiddleware``) there's
an optional setting ``ARGUS_REMOTE_USER_METHOD_NAME`` to choose what to show on
the button.

It can be set via an environment variable of the same name.

OpenIdConnectAuth
~~~~~~~~~~~~~~~~~

If using ``social_core.backends.open_id_connect.OpenIdConnectAuth`` there's an
optional setting ``ARGUS_OIDC_METHOD_NAME`` to choose what to show on the
button.

It can be set via an environment variable of the same name.

Page size
---------

By default, incidents are shown with a page size of ``10`` (ie. 10 rows at
a time), and the user can select a different page size from ``[10, 20, 50,
100]``. It possible to override these settings by setting the
:setting:`ARGUS_INCIDENTS_DEFAULT_PAGE_SIZE` (an integer) and
:setting:`ARGUS_INCIDENTS_PAGE_SIZES` setting respectively.

Incident table column customization
-----------------------------------

You can customize which columns are shown in the incidents listing table by
overriding the :setting:`INCIDENT_TABLE_COLUMNS` setting. See
:ref:`customize-htmx-frontend` for examples.

Themes
------

If you wish to change the available themes, first make sure the support for
Tailwind CSS and daisyUI has been installed, then see
:ref:`customize-htmx-frontend`.

Customization
=============

See :ref:`customize-htmx-frontend`.
