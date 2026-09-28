===================================================
Checking that Argus is up and running and reachable
===================================================

It is useful to be able to easily, cheaply and automatically verify that the
server is up and running. This is called doing a "health check" or "pinging".

Argus has a specific endpoint for this: ``/.still-alive/``. It will always
return HTTP status code 204, and an empty body. It is idempotent, needs no
authentication and can safely be accessed with any HTTP method.

If Argus is served from a sub-path of a domain, the endpoint moves with the
rest of the site: with ``ARGUS_FRONTEND_SUBURL`` set to ``argus``, it is at
``/argus/.still-alive/``. See :ref:`running-argus-below-a-sub-path`.

You might want to exclude log lines for visiting ``/.still-alive/`` as they can
add a lot of noise to an access log.
