.. _running-argus-below-a-sub-path:

=====================================
Running Argus below a sub-path
=====================================

Argus is normally served from the root of a domain, as
``https://argus.example.org/``. It can instead be served from a sub-path of a
domain it shares with something else, as ``https://example.org/argus/``, by
setting the :setting:`ARGUS_FRONTEND_SUBURL` environment variable::

    ARGUS_FRONTEND_SUBURL=argus

One prefix covers the entire site. The frontend moves to ``/argus/``, and with
it the API to ``/argus/api/``, the admin to ``/argus/admin/``, the static files
to ``/argus/static/`` and the health check to ``/argus/.still-alive/``.

The reverse proxy must not strip the prefix
===========================================

Argus generates URLs that contain the sub-path, so whatever sits in front of it
has to pass requests through with the prefix intact. A proxy configured to
strip ``/argus`` before forwarding will produce a site whose links all point at
paths the proxy no longer recognises.

Do not configure the sub-path twice
===================================

Django honours a ``SCRIPT_NAME`` supplied by the WSGI environment, which is how
a mount point declared by uWSGI, gunicorn or the proxy reaches the application.
Argus adds :setting:`ARGUS_FRONTEND_SUBURL` on top of that, so configuring both
moves the site a level deeper than either of them says.

A server mounted at ``/argus`` strips that much of the path before handing the
request over, so with the setting *also* naming ``argus``, a request for
``/argus/incidents/`` arrives looking like ``/incidents/`` and matches nothing:
the site answers 404 at its own documented address. It is reachable only at
``/argus/argus/incidents/``, and every URL it generates carries the doubled
prefix along with it.

Set exactly one of the two. Argus does not set Django's ``FORCE_SCRIPT_NAME``,
which would be the way to make it ignore a mount point it did not ask for.

Cookies are shared with whatever else lives on the domain
=========================================================

Cookies are scoped to a host, not to a path prefix. An application at
``https://example.org/`` and an Argus at ``https://example.org/argus/`` are the
same origin as far as the browser is concerned, so a cookie either of them sets
with the same name as the other will overwrite it.

Argus uses Django's default cookie names, ``sessionid`` and ``csrftoken``. If
the application at the domain root is also a Django site using its defaults,
give one of them different names, for instance in Argus's ``localsettings.py``::

    SESSION_COOKIE_NAME = "argus_sessionid"
    CSRF_COOKIE_NAME = "argus_csrftoken"

Scoping the cookie path instead is not enough. When two cookies of the same
name arrive, browsers generally send the one with the longer path first, and
Django keeps the last value it sees, so the root application's cookie tends to
win regardless.

The symptoms are worth recognising, because neither points at cookies: users
appear to be logged out of one application at random, or form submissions fail
with a CSRF verification error.

Authenticating with OpenID Connect
==================================

The redirect URI Argus hands its identity provider is derived from the
urlconf, so it follows the sub-path automatically. The URI registered with the
provider is not, and has to be updated to match, for instance from
``https://example.org/oidc/complete/oidc/`` to
``https://example.org/argus/oidc/complete/oidc/``.

Permalinks in notifications and tickets
=======================================

:setting:`ARGUS_FRONTEND_URL` is used to build links back to Argus from
notifications and tickets. The sub-path is appended to it automatically, so
both ``https://example.org`` and ``https://example.org/argus`` yield permalinks
below ``https://example.org/argus/``.
