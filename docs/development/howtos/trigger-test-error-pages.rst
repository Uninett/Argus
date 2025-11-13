===============================
How to trigger test error pages
===============================

To test Django's error views in Argus, the following endpoint can be used:

``/.error/?status-code=<error_code>``

Replace ``<error_code>`` with one of the supported HTML error codes: 400, 401, 403, 404, 410, or 500.

Notes
~~~~~
- DEBUG must be set to False in the Django settings to view the standard error pages.
- Status codes ``404`` and ``500`` will trigger relevant exceptions, which in turn send messages to the user in the main view.
