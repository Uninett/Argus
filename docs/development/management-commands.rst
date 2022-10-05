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
