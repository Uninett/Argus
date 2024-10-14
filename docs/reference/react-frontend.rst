.. _react-frontend:

==============
REACT Frontend
==============

Settings
========

Base the settings file on ``argus.spa.settings``. The individual settings are
in ``argus.spa.spa_settings``, note especially that :setting:`ROOT_URLS` is set
to ``argus.spa.urls``. If you prefer to make your own root ``urls.py``, the
frontend-specific urls can be imported from ``argus.spa.spa_urls``.

Domain settings
---------------

.. setting:: ARGUS_COOKIE_DOMAIN

* :setting:`ARGUS_COOKIE_DOMAIN` holds the domain of the Argus instance. This is the domain
  that the cookie is set for. It is needed to log into the frontend.

.. setting:: ARGUS_FRONTEND_URL

* :setting:`ARGUS_FRONTEND_URL` is used for redirecting back to frontend after logging in
  through Feide and CORS. Must either be a subdomain of or the same as
  :setting:`ARGUS_COOKIE_DOMAIN`.

In production, Argus requires the frontend and the backend to either be
deployed on the same domain, or the frontend to be on a subdomain of the
:setting:`ARGUS_COOKIE_DOMAIN`. When running Argus on localhost for development
and testing, :setting:`ARGUS_COOKIE_DOMAIN` can be empty (and will default to
localhost).

Dataporten via OAuth2
---------------------

.. setting:: ARGUS_DATAPORTEN_KEY

* :setting:`ARGUS_DATAPORTEN_KEY` holds the id/key for using dataporten for authentication.

.. setting:: ARGUS_DATAPORTEN_SECRET

* :setting:`ARGUS_DATAPORTEN_SECRET` holds the dataporten password.

Refer to the section :ref:`dataporten <dataporten-reference>` for more information.
