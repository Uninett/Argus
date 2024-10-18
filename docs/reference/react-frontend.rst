.. _react-frontend:

==============
REACT Frontend
==============

The classic frontend is a single page application (SPA) written in REACT. See
the `Github repo of Argus-frontend <https://github.com/uninett/Argus-frontend>`_

It needs its own specific settings and has a handful of API endpoints that are
not needed if running headless.

Settings
========

Base the settings file on ``argus.spa.settings``. The individual settings are
in ``argus.spa.spa_settings``, note especially that :setting:`ROOT_URLCONF` is set
to ``argus.spa.urls``. If you prefer to make your own root ``urls.py``, the
frontend-specific urls can be imported from ``argus.spa.spa_urls``.

Domain settings
---------------

.. setting:: ARGUS_SPA_COOKIE_DOMAIN

* :setting:`ARGUS_SPA_COOKIE_DOMAIN` holds the domain of the Argus instance. This is the domain
  that the cookie is set for. It is needed to log into the frontend.

.. setting:: ARGUS_FRONTEND_URL

* :setting:`ARGUS_FRONTEND_URL` is used for redirecting back to frontend after logging in
  through Feide and CORS. Must either be a subdomain of or the same as
  :setting:`ARGUS_SPA_COOKIE_DOMAIN`.

In production, Argus requires the frontend and the backend to either be
deployed on the same domain, or the frontend to be on a subdomain of the
:setting:`ARGUS_SPA_COOKIE_DOMAIN`. When running Argus on localhost for
development and testing using the `dev`, `dockerdev` or `test_CI` settings-file
as a base, :setting:`ARGUS_SPA_COOKIE_DOMAIN` can be empty (and will default to
localhost).

Dataporten via OAuth2
---------------------

.. setting:: ARGUS_DATAPORTEN_KEY

* :setting:`ARGUS_DATAPORTEN_KEY` holds the id/key for using dataporten for authentication.

.. setting:: ARGUS_DATAPORTEN_SECRET

* :setting:`ARGUS_DATAPORTEN_SECRET` holds the dataporten password.

Refer to the section :ref:`dataporten <dataporten-reference>` for more information.

API Endpoints
=============

The following endpoints are only used by this frontend:

* ``/login-methods/``
* ``/api/v1/login/``
* ``/api/v2/login/``
* ``/api/v1/logout/``
* ``/api/v2/logout/``

Furthermore, visiting ``/oidc/login/dataporten_feide/`` when dataporten is set
up will trigger a login via dataporten.
