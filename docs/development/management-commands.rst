.. _management-commands:

===================
Management commands
===================

This section will talk about all available management commands that Argus offers.

.. _initial-setup:

Initial setup
-------------

To create the standard instances and fill any lookup tables one can use
the command `initial_setup`:

    .. code:: console

        $ python manage.py initial_setup

See the inbuilt help for flags and toggles:

    .. code:: console

        $ python manage.py initial_setup --help

To set the email address of the created admin user, which by default is not
set, add the `-e` flag to the command as such:

    .. code:: console

        $ python manage.py initial_setup -e "admin@example.com"

To set the user name of the created admin user, which by default is `admin`,
add the `-u` flag to the command as such:

    .. code:: console

        $ python manage.py initial_setup -u "Name"

To set the password of the created admin user add the `-p` flag to the command
as such:

    .. code:: console

        $ python manage.py initial_setup -p "secure-password"

.. _generate-secret-key:

Generate a secret key
---------------------

To generate a secret key to be used in the `cmd.sh` file one can use
the command `gen_secret_key`:

    .. code:: console

        $ python manage.py gen_secret_key

.. warning:: Keep the :setting:`SECRET_KEY` secret, as it is relevant to the
    security and integrity of your Argus instance.


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


.. _create-source:

Create source
-------------

To create a new source system in the database for testing purposes one can use
the command `create_source`:

    .. code:: console

        $ python manage.py create_source

See the inbuilt help for flags and toggles:

    .. code:: console

        $ python manage.py create_source --help

This command takes the name for the new source as an argument, if none is
given, the name will be `argus`:

    .. code:: console

        $ python manage.py create_source "Source name"

To add a custom source system type, instead of the default `argus`, add the
`-t` flag to the command as such:

    .. code:: console

        $ python manage.py create_source -t "Custom type"


.. _check-token-expiry:

Check for token expiry
----------------------

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

Also if an expiry incident is found for which the referenced token is not close
to expiring anymore this incident will be closed. This can happen when the
variable ``AUTH_TOKEN_EXPIRES_AFTER_DAYS`` in :ref:`site-specific-settings`
is changed.

This incident will automatically be closed if the token related to the incident
is renewed, deleted or replaced by a new one.


.. _toggle-profile-activation:

Toggle profile activation
-------------------------
.. warning::
    You should be careful using the `toggle_profile_activation` command in a
    production environment, since activating previously inactive notification profiles
    can lead to notifications, and deactivating a previously active profile might lead to
    missing notifications.

To quickly make a notification profile (in)active one can use the command
`toggle_profile_activation`:

    .. code:: console

        $ python manage.py toggle_profile_activation

See the inbuilt help for flags and toggles:

    .. code:: console

        $ python manage.py toggle_profile_activation --help

This command takes a list of notification profile ids (separated by spaces) as
arguments:

    .. code:: console

        $ python manage.py toggle_profile_activation 1 2 3 4

It will lead to an error if no ids are given.


.. _stresstest:

Stresstest
----------
.. warning::
    You should be careful using the `stresstest` command against a production environment,
    as the incidents created during the stresstest can trigger notifications
    like any other real incidents.

You can run stresstests against the incident creation API with the command `stresstest`:

    .. code:: console

        $ python manage.py stresstest

The stresstest will create as many incidents as it can during a given timespan by
sending requests to the incident creation API. Afterwards, it will verify that the
incidents added to the database by the stresstest were created correctly.

`stresstest` requires a URL to the target host and a token related to a source system
as positional arguments. The URL can point to a local or remote argus instance.
A valid token can be generated via the Django admin interface.

Example usage pointing to a local testing instance of Argus:

    .. code:: console

        $ python manage.py stresstest http://localhost:8000 $TOKEN

See the inbuilt help for flags and toggles:

    .. code:: console

        $ python manage.py stresstest --help

The duration of the stresstest in seconds can be set using the `-s` flag:

    .. code:: console

        $ python manage.py stresstest http://localhost:8000 $TOKEN -s 10

Timeout of requests in seconds can be set with the `-t` flag:

    .. code:: console

        $ python manage.py stresstest http://localhost:8000 $TOKEN -t 5


Multiple asynchronous workers can be used to send requests in parallel
using the -w flag:

    .. code:: console

        $ python manage.py stresstest http://localhost:8000 $TOKEN -w 5

The created incidents can be bulk ACKed at the end of the test by setting
the `-b` flag:

    .. code:: console

        $ python manage.py stresstest http://localhost:8000 $TOKEN -b


If you are running Argus inside a Docker container, the stresstest can be run with:

    .. code:: console

        $ docker compose exec api python manage.py stresstest
