.. _management-commands:

===================
Management commands
===================

This section will talk about all available management commands that Argus offers.

Setup helpers
=============

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

Troubleshooting helpers
=======================

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

To use a different source than 'argus' add the `-s` flag to the command as
such:

    .. code:: console

        $ python manage.py create_fake_incident -s "Notargus"

To also set the type of that different source add the `--source-type` flag to
the command as such:

    .. code:: console

        $ python manage.py create_fake_incident -s "Notargus" --source-type "type"

To set the level of the incident add the `-l` flag to the command as such
and choose a level between 1 and 5 (1 being the highest severity, 5 the
lowest):

    .. code:: console

        $ python manage.py create_fake_incident -l 2

To add more tags to the incident add the `-t` flag to the command and
tags of the form `key=value` (add multiple separated by a space):

    .. code:: console

        $ python manage.py create_fake_incident -t a=b c=d

To add metadata to the incident either add the `--metadata` flag to the
command and metadata in JSON format as such:

    .. code:: console

        $ python manage.py create_fake_incident --metadata "{'a':'b'}"

Or to use a JSON file use the `--metadata-file` flag as such:

    .. code:: console

        $ python manage.py create_fake_incident --metadata-file "a.json"

And if the incident should be stateless add the flag `--stateless`:

    .. code:: console

        $ python manage.py create_fake_incident --stateless

Instead of setting all these arguments on the command line it is also possible
to use the flag `-f` and give a list of json files that contain all data as
such:

    .. code:: console

        $ python manage.py create_fake_incident --files "a.json" "b.json"

This gives also a wider range of attributes that can be set, in addition to the
previously mentioned ones it is possible to set start time, end time, source
incident id, details url and ticket url.

(The same command is well-suited to manually test the notification system: Make
a filter that matches fake incidents, for instance by setting `source` to
`argus`, and create a single fake incident.)

.. _close-incident:

Close incident
--------------

To close one or more incidents one can use the command `close_incident`:

    .. code:: console

        $ python manage.py close_incident

See the inbuilt help for flags and toggles:

    .. code:: console

        $ python manage.py close_incident --help

This command takes either the id of the incident that should be closed as an
argument:

    .. code:: console

        $ python manage.py close_incident --id 1234

Or the source and the source incident id that can be used to find the incident:

    .. code:: console

        $ python manage.py close_incident --source "argus" --source-incident-id 1234

To only close the incident if it is older than a given duration add the
`--duration` flag to the command as such:

    .. code:: console

        $ python manage.py close_incident --id 1234 --duration "01:05:00"

To add a specific message to the closing event add the `--closing-message` flag
to the command as such:

    .. code:: console

        $ python manage.py close_incident --id 1234 --closing-message "Testing that closing works"

You can also close one or multiple incidents by giving a list of json files
that contain the information, at least id or source + source incident id need
to be included. An example file would look as such:

    .. code-block:: JSON

        {
            "source_incident_id": "1234",
            "source": "source name",
            "duration": "01:05:00"
        }

And the flag `--files` would be used as such:

    .. code:: console

        $ python manage.py close_incident --files path-to-json-file.json path-to-other-json-file.json


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
==========
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

User management
===============

Create a new user
-----------------

There's a command ``createuser`` that can do this.

Full signature is:

.. code:: console

   $ python manage.py createuser USERNAME -p PASSWORD -e EMAIL -f FIRST_NAME -l LAST_NAME --is-active --is-staff --is-superuser

Only a username is needed to create a user, but in order for the user to be able
to log in both ``--is-active`` and a password must be set.

If ``--is-superuser`` is included, ``--is-staff`` will also be set. Just
setting ``--is-staff`` will grant access to the admin.

Instead of using the ``-p`` argument to set a password you can also set the
environment variable ``DJANGO_USER_PASSWORD``.

Change an existing user
-----------------------

The Swiss Army Knife command for this is ``changeuser``.

Full signature is:

.. code:: console

   $ python manage.py changeuser USERNAME -p PASSWORD -e EMAIL -f FIRST_NAME -l LAST_NAME (-a | -d) (--staff | --nostaff) (--superuser | --nosuperuser)

The flags ``-a`` and ``-d`` are mutually exclusive and activates or deactivates
a user respectively.

To deactivate a user run:

.. code:: console

   $ python manage.py changeuser USERNAME -d

This will both deactivate the user **and** scramble their password, so on
reactivation they need to set a new password.

To (re)activate a user run:

.. code:: console

   $ python manage.py changeuser USERNAME -a

This *will not* set a password if one has not already been set.

Instead of using the ``-p`` argument to set a password you can also set the
environment variable ``DJANGO_USER_PASSWORD``.

The flags ``--staff`` and ``--nostaff`` are mutually exclusive and controls
whether the user has access to the admin (staff) or not (nostaff).

The flags ``--superuser`` and ``--nosuperuser`` are mutually exclusive and controls
whether the user is a superuser (superuser) or not (nosuperuser). Superusers
have by default access to the admin, but this can be turned off with
``--nostaff``.

Deprecated/overlapping commands
===============================

Grant superuser status to a user
--------------------------------

There is a command ``grantsuperuser`` but you might as well use ``changeuser``
instead, like so:

.. code:: console

   $ python manage.py changeuser USERNAME --superuser


Revoke superuser status from a user
-----------------------------------

There is a command ``revokesuperuser`` but you might as well use ``changeuser``
instead, like so:

.. code:: console

   $ python manage.py changeuser USERNAME --nosuperuser

Create a superuser
------------------

Django ships with a command ``createsuperuser`` but you might as well use
``createuser`` instead, like so:

.. code:: console

   $ python manage.py createuser USERNAME --is-superuser

Set a password
--------------

There is a command ``setpassword`` but you might as well use ``changeuser``
instead, like so:

.. code:: console

   $ python manage.py changeuser USERNAME -p PASSWORD

Instead of using the ``-p``-flag you can set the environment variable
``DJANGO_USER_PASSWORD``.

Change a password
-----------------

Django ships with a command ``changepassword`` but you might as well use
``changeuser`` instead, like so:

.. code:: console

   $ python manage.py changeuser USERNAME -p PASSWORD

Instead of using the ``-p``-flag you can set the environment variable
``DJANGO_USER_PASSWORD``.
