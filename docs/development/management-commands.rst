.. _management-commands:

===================
Management commands
===================

This section will talk about all available management commands that Argus offers.

.. _check-token-expiry:

Check for token expiry
--------------------------------------------

One can check if any of the tokens that are connected to a source system will
expire soon with the management command `check_token_expiry`:

    .. code:: console

        $ python manage.py check_token_expiry

See the inbuilt help for flags and toggles:

    .. code:: console

        $ python manage.py check_token_expiry --help

By default `check_token_expiry` checks if any token will expire within in the
next 7 days. To change that default one can use the `-d`-flag and give a
different number of days:

    .. code:: console

        $ python manage.py check_token_expiry -d 14

In case any of the existing tokens, which are connected to a source system,
will expire within the next given number of days, Argus will post an incident
to let the user know.

This incident will automatically be closed if the token related to the incident
is renewed, deleted or replaced by a new one.
