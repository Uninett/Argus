===================
argus-HTMx-frontend
===================

Experimental frontend for `argus-server`_ as a django app.

Will possibly cease to exist as a separate app if the experiment is deemed
successful.

See `argus-server`_ for more about argus.

Imports `django-htmx`_. See the `documentation for django-htmx`_
for details.

How to play
===========

Install
-------

To make sure you do not accidentally work on an old argus-server, do the following:

1. Use/make a venv, for instance: create a new one with ``python -m venv argus-htmx``
2. Check out argus-server code
3. Install argus-server dynamically into the venv: ``pip install -e .``
4. Check out this repo
5. Install this app dynamically into the venv: ``pip install -e .``

It is now safe to remove argus-server from the venv if you feel like it.

Configure
---------

Do this in your workdir, which could be the checked out `argus-server`_ repo.

Django-style
~~~~~~~~~~~~

In your local settings that star-imports from an `argus-server`_ settings file::

    INSTALLED_APPS += [
        "django_htmx",
        "argus_htmx",
        "widget_tweaks",
    ]
    ROOT_URLCONF = "urls"
    MIDDLEWARE += ["django_htmx.middleware.HtmxMiddleware"]

In the same file, add a copy of the entirety of ``TEMPLATES``. Choose one of
the functions in ``argus_htmx.context_processors``. In the entry for
``django.template.backends.django.DjangoTemplates``, append the full dotted
path to the end of the ``context_processors`` list.

Next to ``localsettings.py`` create an ``urls.py`` containing::

   from django.urls import path, include

   from argus.site.urls import urlpatterns

   urlpatterns += [
       path("", include("argus_htmx.urls"))
   ]

With EXTRA_APPS
~~~~~~~~~~~~~~~

Choose one of the functions in ``argus_htmx.context_processors``, exemplified
by "theme_via_GET" below.

In your environment variables::

    ARGUS_EXTRA_APPS = '[{"app_name": "django_htmx"}, {"app_name": "argus_htmx", "urls": {"path": "", "urlpatterns_module": "argus_htmx.urls"}, "context_processors": ["argus_htmx.context_processor.theme_via_GET"]}, {"app_name": "widget_tweaks"}]'

In your local settings that star-imports from an `argus-server`_ settings file::

    MIDDLEWARE += ["django_htmx.middleware.HtmxMiddleware"]

Update
------

On every new version, reinstall the dependencies since there might be new ones.

Themes and styling
------------------

To try out class-less themes use the context processor
``argus_htmx.context_processor.theme_via_session`` instead of
``argus_htmx.context_processor.theme_via_GET``.

Default included themes are: `light`, `dark` and `argus`.

This project supports Tailwind CSS utility classes and daisyUI components for styling.
Below is an overview of the stack, installation and build instructions, and configuration details for themes and styles.

Overview
~~~~~~~~
* Tailwind CSS: A utility-first CSS framework for rapidly building custom user interfaces.
* daisyUI: A component library for Tailwind CSS that provides a set of ready-to-use components as well as color themes.

Installation and build instructions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Recommended but open for tweaks and adaptations steps:

1. Get Tailwind standalone CLI bundled with daisyUI from
   https://github.com/dobicinaitis/tailwind-cli-extra

   Most linux::

        $ curl -sL https://github.com/dobicinaitis/tailwind-cli-extra/releases/latest/download/tailwindcss-extra-linux-x64 -o /tmp/tailwindcss
        $ chmod +x /tmp/tailwindcss

   For other OSes see
   https://github.com/dobicinaitis/tailwind-cli-extra/releases/latest/ and
   update the bit after ``download/`` accordingly.

   Optionally you can compile tailwind+daisyUI standalone cli bundle yourself as described here:
   https://github.com/tailwindlabs/tailwindcss/discussions/12294#discussioncomment-8268378.
2. (Linux/OsX) Move the tailwindcss file to your $PATH, for instance to ``~/bin/`` or ``.local/bin``.
3. Go to the repo directory (parent of ``src/``)
4. Build main stylesheet file using ``tailwindcss`` executable from step 1 and pointing to the included config file::

        tailwindcss -c src/argus_htmx/tailwind/tailwind.config.js -i src/argus_htmx/tailwind/styles.css --output src/argus_htmx/static/styles.css

   We recommend running this is in a separate terminal with the ``--watch``
   flag so that the "styles.css" file is auto-updated when you save a template.


Customization
~~~~~~~~~~~~~

How to customize the look:


*  Override Argus' Tailwind CSS theme defaults and/or choose which daisyUI
   color themes to include. You can do so by updating the default
   ``TAILWIND_THEME_OVERRIDE`` and ``DAISYUI_THEMES`` values respectively
   before running a ``tailwind_config`` management command:

  Via environment variables, for example::

    TAILWIND_THEME_OVERRIDE = '
      {
        "borderWidth": {
          "DEFAULT": "1px"
        },
        "extend": {
          "borderRadius": {
            "4xl": "2rem"
          }
        }
      }
    '
    DAISYUI_THEMES = '
      [
        "light",
        "dark",
        "cyberpunk",
        "dim",
        "autumn",
        { "mytheme": {
            "primary": "#009eb6",
            "primary-content": "#00090c",
            "secondary": "#00ac00",
            "secondary-content": "#000b00",
            "accent": "#ff0000",
            "accent-content": "#160000",
            "neutral": "#262c0e",
            "neutral-content": "#cfd1ca",
            "base-100": "#292129",
            "base-200": "#221b22",
            "base-300": "#1c161c",
            "base-content": "#d0cdd0",
            "info": "#00feff",
            "info-content": "#001616",
            "success": "#b1ea50",
            "success-content": "#0c1302",
            "warning": "#d86d00",
            "warning-content": "#110400",
            "error": "#ff6280",
            "error-content": "#160306"
            }
        }
      ]
    '

  Or by providing corresponding values in your local settings that star-imports from an `argus-server`_ settings file::

        TAILWIND_THEME_OVERRIDE = {...}
        DAISYUI_THEMES = [...]

  Some links that may be relevant for the customization values mentioned above:
    * `daisyUI themes`_
    * `list of daisyUI color names`_
    * `Tailwind CSS theme customization`_

*  Override the default main stylesheet path by providing a ``path_to_stylesheet`` value in a template ``context``.
*  Include additional styles/stylesheets using ``head`` block in your templates.
*  Generate Tailwind config file by running ``tailwind_config`` management
   command. By default the generated file will be based on
   ``src/argus_htmx/tailwindtheme/tailwind.config.template.js`` and expected
   values will be injected with reasonable defaults.

UI Settings
-----------

Incident table column customization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can customize which columns are shown in the incidents listing table by overriding the
``INCIDENT_TABLE_COLUMNS`` setting. This setting takes a list of ``str`` or
``argus_htmx.incidents.customization.IncidentTableColumn`` instances. when given a ``str``, this
key must be available in the ``argus_htmx.incidents.customization.BUILTIN_COLUMNS`` dictionary. For
example::

    from argus_htmx.incidents.customization import BUILTIN_COLUMNS, IncidentTableColumn

    INCIDENT_TABLE_COLUMNS = [
        "id",
        "start_time",
        BUILTIN_COLUMNS["description"], # equivalent to just "description"
        IncidentTableColumn( # a new column definition
            name="name",
            label="Custom"
            cell_template="/path/to/template.html"
            context={
                "additional": "value"
            }
        ),

    ]

For inbuilt support for other types of columns see the howtos in `the local docs <docs/howtos/>`_.


.. _django-htmx: https://github.com/adamchainz/django-htmx
.. _argus-server: https://github.com/Uninett/Argus
.. _documentation for django-htmx: https://django-htmx.readthedocs.io/en/latest/
.. _daisyUI themes: https://daisyui.com/docs/themes/
.. _list of daisyUI color names: https://daisyui.com/docs/colors/#-2
.. _tailwind-cli-extra: https://github.com/dobicinaitis/tailwind-cli-extra
.. _Tailwind CSS theme customization: https://tailwindcss.com/docs/theme
