.. _authentication-reference:

==============
Authentication
==============

Username/password
=================

Argus supports API login with username and password, see :ref:`api-auth-endpoints`.
This will yield a bearer token.

Also supported is logging in via browser to the admin, at ``/admin/``. This
will set a session cookie.

..
   User controlled via webserver
   =============================

   Some web servers have have plugins that talk various authentication
   protocols like SAML, OAuth2 and others, typically setting an environment
   variable REMOTE_USER. Django has built in support for this by adding
   ``"django.contrib.auth.middleware.RemoteUserMiddleware`` to the
   :setting:`MIDDLEWARE`-setting and
   ``django.contrib.auth.backends.RemoteUserBackend`` to the
   :setting:`AUTHENTICATION_BACKENDS`/setting.

.. _oauth2:

OAuth2
======

For support of OAuth2/OIDC-logins, the library `python-social-auth (PSA)`_ is
used. By adding a new backend to the setting :setting:`AUTHENTICATION_BACKENDS` it is
possible to support all that PSA supports, and it is also not too hard to write
your own.

Each backend will need a client key and secret, see the documentation for each
backend.

Which backends are configured will be available on the JSON endpoint
``/login-methods/``.


.. _dataporten-reference:

Dataporten
----------

Out of the box, Argus supports user authentication via Dataporten.


Dataporten registration
~~~~~~~~~~~~~~~~~~~~~~~

Visit https://dashboard.dataporten.no/ for more information or to create a new
application.


Dataporten setup in Argus
~~~~~~~~~~~~~~~~~~~~~~~~~

In Argus, register a new application with the following redirect URL:
  ``{server_url}/oidc/complete/dataporten_feide/``

Replace ``{server_url}`` with the URL to the server running this project, like
``http://localhost:8000``

Now add the following permission scopes:
 * ``profile``
 * ``userid``
 * ``userid-feide``
 * ``email``

.. _python-social-auth (PSA): https://python-social-auth.readthedocs.io/en/latest/
