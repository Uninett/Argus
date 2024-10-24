.. _htmx-frontend:

=============
HTMx Frontend
=============

The new frontend is old-new school and uses HTMx to boost HTML pages. See the
`Github repo of argus-htmx-frontend <https://github.com/uninett/argus-htmx-frontend>`_

It has its own specific settings and currently depends on an app.

It is not needed if running headless.

Setup
=====

Production
----------

Install the app directly::

    pip install argus-frontend-htmx

... or indirectly via argus-server::

    pip install argus-server[htmx]

Development
-----------

If you're working just on argus-server::

    cd argus-server-repo && pip install -e .[htmx]

This will install the frontend as a package and it will not be editable.

If you're working just on argus-frontend-htmx::

    cd argus-htmx-repo && pip install -e .

This will install the server as a package and it will not be editable.

If you want to work on both in tandem::

    cd argus-htmx-repo && pip install -e .
    cd argus-server-repo && pip uninstall argus-server && pip install -e .

Since argus-frontend-htmx depends on argus-server it will install the latter
from a package, which is probably not what you want. That's why it might be
necessary to uninstall the package before you install the editable version you
will be working on. If you install argus-server first, then installing the
frontend will still drag in the argus-server package since pip doesn't
understand the the package and the editable install does the same job.

Settings
========

If you don't need to override any settings with a file at all (maybe there are
environment variables for everything you need to change) you can use
``argus.htmx.settings`` directly. If not, copy the contents of
``argus.htmx.settings`` into the top of your tuned settings file.

We mutate some of the existing settings with the same system used for extra
apps and overriding apps so have a look at ``argus_htmx.appconfig`` for the
individual settings. Note especially that :setting:`ROOT_URLCONF` is set to
``argus.htmx.urls``. If you prefer to make your own root ``urls.py``, the
frontend-specific urls can be imported from ``argus.htmx.htmx_urls``.

Domain settings
---------------

.. setting:: ARGUS_FRONTEND_URL

* :setting:`ARGUS_FRONTEND_URL` is used for building permalinks to point back
  to incidents in the dashboard.

The setting must point to the publicly visible domain where the frontend is
running. This might be different from where the backend is running.

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

Use the python social auth backend
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
