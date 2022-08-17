.. _management-commands:

===================
Management commands
===================

This section will talk about all available management commands that Argus offers.

.. _create-fake-incident:

Create fake incidents
---------------------

To fill the database with fake incidents for testing purposes one can use
the command `create_fake_incident`:

    .. code:: console

        $ python manage.py create_fake_incident

See the inbuilt help for flags and toggles:

    .. code:: console

        $ python manage.py create_fake_incident --help

By default `create_fake_incident` creates an open stateful incident.

To create multiple incidents one can use the `-b` flag and determine the
number of incidents:

    .. code:: console

        $ python manage.py create_fake_incident -b 15

To add a custom description add the `-d` flag to the command as such:

    .. code:: console

        $ python manage.py create_fake_incident -d "Custom description"

To set the level of the incident add the `-l` flag to the command as such
and choose a level between 1 and 5 (1 being the highest severity, 5 the
lowest):

    .. code:: console

        $ python manage.py create_fake_incident -l 2

To add more tags to the incident add the `-t` flag to the command and
tags of the form `key=value` (add multiple separated by a space):

    .. code:: console

        $ python manage.py create_fake_incident -t a=b c=d

And if the incident should be stateless add the flag `--stateless`:

    .. code:: console

        $ python manage.py create_fake_incident --stateless

(The same command is well-suited to manually test the notification system: Make
a filter that matches fake incidents, for instance by setting `source` to
`argus`, and create a single fake incident.)


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
