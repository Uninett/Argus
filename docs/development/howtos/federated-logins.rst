===================================
How to add federated login (OAuth2)
===================================

We use the 3rd party framework `python-social-auth`_, aka. ``PSA``, for
handling logins/logouts via OAuth2. The relevant dependencies are
`social-auth-core` and `social-auth-app-django`. We haven't as of yet tried
`social-auth-core[saml]` for SAML or `social-auth-core[openidconnect]` for
OIDC.

The settings-files add support for easier configuration of the OAuth2 provider
we use ourselves but you can add similar support for your chosen provider.

Choose an OAUth2-provider
=========================

Have a look at the list of providers included with ``PSA`` at `PSA's list of supported providers
<https://python-social-auth.readthedocs.io/en/latest/backends/index.html#supported-backends>`_.

Our default provider ``Feide via OAuth2`` is vendored into the Argus source
code, the backend path is ``argus.dataporten.social.DataportenFeideOAuth2``.

Add the backend path of your chosen provider to the start of the Django setting
:setting:`AUTHENTICATION_BACKENDS`.

We'll use the GitHub OAuth2-provider for users as an example for the rest of
this howto. The backend path is ``social_core.backends.github.GithubOAuth2``.

Get the key and secret for the provider
=======================================

You need to set two Django settings per provider in addition to updating
:setting:`AUTHENTICATION_BACKENDS`, these are backend-dependent, for our
example they are:

* SOCIAL_AUTH_GITHUB_KEY
* SOCIAL_AUTH_GITHIB_SECRET

The "GITHUB"-part is the one that varies.

How to get these differs between backends. With GitHub you need a GitHub user.
See `Github: Creating an OAuth app <https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app>`_
for how to get the key and secret for GitHub.

Github wants a callback url when configuring OAuth2, this will always be
``https://YOURDOMAIN/oidc/``. Github only supports one callback url.

Test
====

Get and test the login url for the backend
------------------------------------------

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
----------------------------------------------

Replace ``login`` in the login-url with ``logout`` to derive the logout url.
Paste the logout url into the url-field of the browser window you are logged
into to test logging out.

.. _python-social-auth: https://github.com/python-social-auth/
