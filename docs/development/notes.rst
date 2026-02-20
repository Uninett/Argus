.. _development:

=================
Development notes
=================

This section will provide some useful hints and tips for developing Argus.


Applying settings and switching between them
--------------------------------------------

As elaborated in :ref:`site-specific-settings`, there are two ways to define settings
in Argus:

1. with environment variables
2. using a ``settings.py`` file.

For development, a simple and good practice is to define environment variables in a
``.env`` file. Copy ``.env.template`` to ``.env`` and fill in the values. The dev
settings (``argus.site.settings.dev``) will automatically load ``.env`` via
``python-dotenv``.

The limitation of environment variables is that they can only contain numbers, Boolean
values (``0``/``1``) and strings.
Use the ``localsettings.py`` file to define settings that require more complex values,
such as conditional expressions, Python dicts and tuples.

Settings in the ``settings.py`` file will override environment variables.
Note that the extra settings-file and ``argus`` have to be in the python path.
We therefore recommend keeping your ``settings.py`` files in the same directory as
``manage.py``.

Settings can be tested in ``localsettings.py`` and moved to the other settings
files later.

.. note:: **Tip**: If you copy the entire logging-setup from "argus.site.settings.dev"
        to ``localsettings.py`` remember to set ``disable_existing_loggers`` to
        ``True``.
        Otherwise, logentries will appear twice.

.. warning:: Do not check your ``.env`` or ``settings.py`` files into version control,
        since they contain passwords and sensitive data.
