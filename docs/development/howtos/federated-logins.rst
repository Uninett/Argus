.. _howto-federated-logins:

==========================
How to add federated login
==========================

Externally by setting REMOTE_USER
=================================

We only know of SAML-support.

* Apache: see mod_auth_mellon
* Nginx: see nginx-saml

Internally with the help of a library
======================================

We use the 3rd party framework `python-social-auth`_, aka. ``PSA``, for
handling federated logins/logouts internally. The minimum dependency is
`social-auth-core`.

The settings-files add support for easier configuration of the OAuth2 provider
we use ourselves but you can add similar support for your chosen provider.

----
SAML
----

See `Python Social Auth SAML
<https://python-social-auth.readthedocs.io/en/latest/backends/saml.html>`_,
which has the additional dependency `social-auth-core[saml]`. We haven't as of
yet tried the SAML-support.

----
OIDC
----

You need to install ``social-auth-core[openidconnect]`` then look at `Python
Social Auth OIDC
<https://python-social-auth.readthedocs.io/en/latest/backends/oidc.html>`_.

------
OAuth2
------

You need to install ``social-auth-app-django``.

Choose an OAUth2-provider
-------------------------

Have a look at the list of providers included with ``PSA`` at `PSA's list of supported providers
<https://python-social-auth.readthedocs.io/en/latest/backends/index.html#supported-backends>`_.

Also be on the lookout for 3rd party providers, we use `python-dataporten-auth
(PyPI) <https://pypi.org/project/python-dataporten-auth/` ourselves.

Add the backend path of your chosen provider to the start of the Django setting
:setting:`AUTHENTICATION_BACKENDS`. eg::

  AUTHENTICATION_BACKENDS = [
    "dataporten.social.DataportenFeideOAuth2",
    "django.contrib.auth.backends.ModelBackend",
  ]

If you want to use ours the environment variables
``SOCIAL_AUTH_DATAPORTEN_KEY`` and ``SOCIAL_AUTH_DATAPORTEN_SECRET`` are used
to make the client id and client secret available to the settings file.

Update urls.py
--------------

The urls in ``social_django.urls`` must be reacahable from the ``urls.py``
pointed to by your :setting:``ROOT_URLCONF`` setting. The
``python-social-auth`` docs state to place the urls directly in your url root,
but for better namespacing/isolation you can add them under ``oidc/``, ie::

  urlpatterns = [
    ...
    path("oidc/", include("social_django.urls", namespace="social")),
    ...
  ]

If you have the development dependencies installed you can check if these
urls are already included via the management command ``show_urls``.

Example: Github Backend
-----------------------

For the rest of this how-to we'll use the GitHub OAuth2-provider for users as
an example. We'll base off of `Python Social Auth: Github backend
<https://python-social-auth.readthedocs.io/en/latest/backends/github.html>`_
with a few minor differences

The backend path is ``social_core.backends.github.GithubOAuth2``::

  AUTHENTICATION_BACKENDS = [
    "social_core.backends.github.GithubOAuth2",
    "django.contrib.auth.backends.ModelBackend",
  ]

Get the key and secret for the provider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, you must create a GH Oauth app. See `Github: Creating an OAuth app <https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app>`_

The Authorization callback url must match the ``social_django.urls`` path in your urlpatterns (ie.
``/oidc``). The protocol, hostname and port must match the deployed Argus instance.

.. note:: Github also supports 127.0.0.1 as a callback url, which is useful during developmeent. In
  that case the port does not need to match, and in fact, you should not specify a port in the
  authorization callback url (ie. ``http://127.0.0.1/oidc``)

Now create client credentials in the applications' settings page.

Update your settings.py with the following keys::

  SOCIAL_AUTH_GITHUB_KEY = <github app client id>
  SOCIAL_AUTH_GITHUB_SECRET = <github app client secret>

These settings differ per authentication backend but generally it is only the ``GITHUB`` part that
changes

Test
----

Get and test the login url for the backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The slug is a backend-specific textual id. Usually it is the name of the
backend in lowercase, so in our example it is ``github``. This is not always the
case and also quite poorly documented.

When all the settings have been set, run Argus locally. The slug is available
through the public JSON endpoint ``/login-methods/``. The ``type`` is "OAuth2".
The ``name`` is the id of the backend. The ``url`` is what we're after.

Visit the url. You should be redirected to GitHub. Log in there, and then be
redirected back. If you are not redirected back correctly first check the
callback url.

Derive and test the logout url for the backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Replace ``login`` in the login-url with ``logout`` to derive the logout url.
Paste the logout url into the url-field of the browser window you are logged
into to test logging out.

.. _python-social-auth: https://github.com/python-social-auth/
