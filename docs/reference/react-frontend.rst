.. _react-frontend:

==============
REACT Frontend
==============

The classic frontend is a single page application (SPA) written in REACT. See
the `Github repo of Argus-frontend <https://github.com/uninett/Argus-frontend>`_

It depends on `redis <https://redis.io/>`_, some additional 3rd party django
apps, needs its own specific settings and has a handful of API endpoints that
are not needed if running headless.

Dependencies
============

Install the python dependencies to talk to redis via ``pip install
argus-server[spa]``.

The docker-compose config included will run up a server for you during
development and testing. How to deploy redis in production will not be detailed
here.

Settings
========

Base the settings file on ``argus.spa.settings``.

The individual settings are in ``argus.spa.spa_settings``, but note:

* :setting:`ROOT_URLCONF` is set to ``argus.spa.root_urls``. If you prefer to
  make your own root ``urls.py``, the frontend-specific urls can be imported
  from ``argus.spa.spa_urls``.
* :setting:`INSTALLED_APPS` is rewritten to add the apps ``channels`` and
  ``argus.spa``. The order matters,``channels`` must be early.

Domain settings
---------------

.. setting:: ARGUS_SPA_COOKIE_DOMAIN

* :setting:`ARGUS_SPA_COOKIE_DOMAIN` holds the domain of the Argus instance. This is the domain
  that the cookie is set for. It is needed to log into the frontend.

.. setting:: ARGUS_FRONTEND_URL

* :setting:`ARGUS_FRONTEND_URL` is used for redirecting back to frontend after logging in
  through Feide and CORS. Must either be a subdomain of or the same as
  :setting:`ARGUS_SPA_COOKIE_DOMAIN`. It is also used for building permalinks
  to point back to incidents in the dashboard, or whenever else an absolute url
  is needed.

Depending on how Argus is deployed this is the only surefire way to get hold
of the externally visible hostname in the code in all cases.

In production, Argus requires the frontend and the backend to either be
deployed on the same domain, or the frontend to be on a subdomain of the
:setting:`ARGUS_SPA_COOKIE_DOMAIN`. When running Argus on localhost for
development and testing using the `dev`, `dockerdev` or `test_CI` settings-file
as a base, :setting:`ARGUS_SPA_COOKIE_DOMAIN` can be empty (and will default to
localhost).

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

.. setting:: CHANNEL_LAYERS

The realtime updates uses the app ``channels``. This setting by default depends
on :setting:`ARGUS_REDIS_SERVER`, itshould normally not be necessary to change
it.

CORS handling
-------------

For the react frontend to have permissions to talk to the backend in
production, CORS headers must be set correctly. See the documentation at
`django-cors-headers <https://pypi.org/project/django-cors-headers/>`_ for what
is possible.

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
