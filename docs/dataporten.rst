.. _dataporten:

==========
Dataporten
==========

Argus supports user authentication via Dataporten.


Dataporten registration
-----------------------

Visit https://dashboard.dataporten.no/ for more information or to create a new
application.


Dataporten setup in Argus
-------------------------

In Argus, register a new application with the following redirect URL:
  ``{server_url}/oidc/complete/dataporten_feide/``

Replace ``{server_url}`` with the URL to the server running this project, like
``http://localhost:8000``

Now add the following permission scopes:
 * ``profile``
 * ``userid``
 * ``userid-feide``
 * ``email``
