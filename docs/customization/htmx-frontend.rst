.. _customize-htmx-frontend:

=============================
Customizing the HTMx frontend
=============================

If you add more pages and endpoints you will have to write your own root
urls.py and set ROOT_URLCONF appropriately.

Adding additional apps
======================

If you have some other apps you want installed and configured, you could either
add the necessary settings to your ``localsettings.py`` or use the extra-apps
machinery. The later is especially useful during the development phase when you
haven't settled on which apps to use yet.

With extra-apps machinery
-------------------------

You make a JSON-file which is read into your settings via one of two
environment variables.

In order to add apps and settings that *extend* ``argus-server`` and this
``app`` you use the environment variable ``ARGUS_EXTRA_APPS``::

    export ARGUS_EXTRA_APPS=`cat extra.json`

If you want to *override* existing apps the environment variable to use is
``ARGUS_OVERRIDING_APPS``::

    export ARGUS_OVERRIDING_APPS=`cat overriding.json`

Have a look at the contents of ``argus.htmx.appconfig._app_settings`` for an
example of what you can set this way.

You can merge your urlpatterns with the apps' urlpatterns via the
``argus.site.utils.get_urlpatterns`` function, see ``argus.htmx.urls`` for an
example.

Themes and styling
==================

How to choose which themes to be made available
-----------------------------------------------

This is controlled by the setting :setting:`DAISYUI_THEMES`. You need to run
the ``tailwind_config`` management command afterwards, followed by ``make
tailwind``.

How to add additional themes
----------------------------

See the `Daisy UI 5 theme generator <https://daisyui.com/theme-generator/>`_
for the themes that are shipped with Argus. You can also generate new themes
there. To add a pre-configured theme just add the name to the
:setting:`DAISYUI_THEMES` setting and run ``tailwind_config`` + ``make
tailwind`` as usual.

If generating a new theme:

1. Make sure the browser is in light mode if making a light theme, or dark mode
   if making a dark theme.
2. Choose a name that is pure ASCII, and don't reuse any of the names that
   comes pre-configured. Save the generated CSS to some file.

The ``argus`` theme is included in the file ``argus/htmx/tailwindtheme/snippets/25-theme-argus.css``. The format is::

    @plugin "daisyui/theme" {
       name: "argus";
       default: false;
       prefersdark: false;
       color-scheme: "light";
       --color-primary: #006d91;
       --color-primary-content: #d1e1e9;
       --color-secondary: #f3b61f;
       --color-secondary-content: #140c00;
       --color-accent: #c84700;
       --color-accent-content: #f8dbd1;
       --color-neutral: #006d91;
       --color-neutral-content: #d1e1e9;
       --color-base-100: #edfaff;
       --color-base-200: #ced9de;
       --color-base-300: #b0babd;
       --color-base-content: #141516;
       --color-info: #0073e5;
       --color-info-content: #000512;
       --color-success: #008700;
       --color-success-content: #d3e7d1;
       --color-warning: #ee4900;
       --color-warning-content: #140200;
       --color-error: #e5545a;
       --color-error-content: #120203;
       /* border radius */
       --radius-selector: 2rem;
       --radius-field: 0.25rem;
       --radius-box: 0.5rem;

       /* base sizes */
       --size-selector: 0.25rem;
       --size-field: 0.25rem;

       /* border size */
       --border: 1px;

       /* effects */
       --depth: 1;
       --noise: 0;
     }

The stuff starting with ``--`` is css-variables.

There are two different methods to install generated themes.

1. Via :setting:`DAISYUI_THEMES`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of adding the name of a theme to the :setting:`DAISYUI_THEMES` setting
you can add an entire theme instead. Given the example theme above, it needs to
be converted to Python like so::

    DAISYUI_THEMES = [
        "light",
        "dark",
        {
            "argus": {
                "name": "argus",
                "default": false",
                "prefersdark": false",
                "color-scheme": "light"",
                "--color-primary": "#006d91",
                "--color-primary-content": "#d1e1e9",
                "--color-secondary": "#f3b61f",
                "--color-secondary-content": "#140c00",
                "--color-accent": "#c84700",
                "--color-accent-content": "#f8dbd1",
                "--color-neutral": "#006d91",
                "--color-neutral-content": "#d1e1e9",
                "--color-base-100": "#edfaff",
                "--color-base-200": "#ced9de",
                "--color-base-300": "#b0babd",
                "--color-base-content": "#141516",
                "--color-info": "#0073e5",
                "--color-info-content": "#000512",
                "--color-success": "#008700",
                "--color-success-content": "#d3e7d1",
                "--color-warning": "#ee4900",
                "--color-warning-content": "#140200",
                "--color-error": "#e5545a",
                "--color-error-content": "#120203",
                "--radius-selector": "2rem",
                "--radius-field": "0.25rem",
                "--radius-box": "0.5rem",
                "--size-selector": "0.25rem",
                "--size-field": "0.25rem",
                "--border": "1px",
                "--depth": "1",
                "--noise": "0",
            },
        },
    ]

Make the above one of the entries in the :setting:`DAISYUI_THEMES` setting and
run ``tailwind_config`` + ``make tailwind`` as usual.

2. Via an app and css snippet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a Django app which has a ``snippets`` directory, see
``argus.htmx.apps.HtmxFrontendConfig.tailwind_css_files`` for something to
copy.

In the snippets-directory, make a new file with the theme you generated before.
We recommend naming the file ``99-theme-THEMENAME.css``, where THEMENAME is the
name you chose when generating the theme.

Add the app to :setting:`INSTALLED_APPS`, the name to
:setting:`DAISYUI_THEMES`, and finish with ``tailwind_config`` + ``make
tailwind`` as usual.

How to customize the look without switching themes
--------------------------------------------------

* Override Argus' Tailwind CSS theme defaults by updating the setting
  :setting:`TAILWIND_THEME_OVERRIDE`.

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

  Or by providing corresponding values in your local settings.

  Run ``tailwind_config`` to generate the configuratonm then ``make tailwind`` to
  generate the final css-file, as usual.

  Some links that may be relevant for the customization values mentioned above:

  * `daisyUI themes`_
  * `list of daisyUI color names`_
  * `Tailwind CSS theme customization`_

* Override the default main stylesheet path by setting
  ``ARGUS_STYLESHEET_PATH`` in the environment. The path is under
  ``STATIC_URL``. This depends on the context processor
  ``argus.htmx.context_processors.path_to_stylesheet``.
* Include additional styles/stylesheets using the ``head`` block in your templates.
* Generate a Tailwind config file by running the ``tailwind_config`` management
  command. It will be placed in
  ``src/argus/htmx/tailwindtheme/tailwind.config.js``. By default the generated
  file will be based on
  ``src/argus/htmx/templates/tailwind/tailwind.config.js`` and expected values
  will be injected with reasonable defaults.

Incident table column customization
===================================

The :setting:`INCIDENT_TABLE_COLUMN_LAYOUTS` setting controls which columns are
shown in the incident table. This setting takes a dictionary where the key is
the name of a layout and the value is a list of ``str`` or
``argus.htmx.incidents.customization.IncidentTableColumn`` instances. when
given a ``str``, this key must be available in the
``argus.htmx.incidents.customization.BUILTIN_COLUMNS`` dictionary. For
example::

    from argus.htmx.incident.columns import BUILTIN_COLUMNS, IncidentTableColumn

    INCIDENT_TABLE_COLUMN_LAYOUTS = {
        "default": [
            "id",
            "start_time",
            BUILTIN_COLUMNS["description"], # equivalent to just "description"
            IncidentTableColumn( # a new column definition
                name="name",
                label="Custom",
                cell_template="/path/to/template.html",  # contents of cell
            ),
        ]
    }

The settings :setting:`INCIDENT_TABLE_COLUMNS` took a single list and is
deprecated. If it exists it is interpreted as a layout named "default".


.. py:class:: IncidentTableColumn

   .. py:attribute:: name

      :type: str

      The identifier for the column

   .. py:attribute:: label

      :type: str

      The column header, put inside ``<th></th>``

   .. py:attribute:: cell_template

      :type: str

      Template to use when rendering a cell for this column.

      For the contents of a cell, put inside ``<td></td>``

   .. py:attribute:: cell_wrapper_template

      :type: str
      :value: htmx/incident/_incident_table_cell_wrapper_default.html

      A template that by default includes the ``cell_template`` and wraps it in
      a ``<td>``-tag. This makes it possible to add attributes to the
      ``<td>``-tag or skip including the ``cell_template`` altogether.

      Deprecated: see ``detail_link``

      Replacing the default with
      ``htmx/incident/_incident_table_cell_wrapper_link_to_details.html`` will
      result in the ``cell_template`` being wrapped in a link (``<a>``) to the
      details page.

   .. py:attribute::detail_link

      :type: bool
      :value: False

      Setting ``detail_link`` to ``True`` will wrap the contents of the cell
      with a link (``<a>``) to the details page.

   .. py:attribute:: column_classes

      :type: str
      :value: ""

      Additional classes to set on ``<th>``, handy for controlling width.

   .. py:attribute:: context

      :type: Optional[dict]
      :value: None

      Additional context to pass to the rendering cell.

   .. py:attribute:: filter_field

      :type: Optional[str]

      When given, this column is considered filterable and a filter input is
      attached to the column header that can provide a query param with
      ``filter_field`` as the key. The key must match a text input form field
      that is recognized by ``incident_list_filter()``.

      Adds a pop-up-able free text search field in the ``<th>``.

   .. py:attribute:: header_template

      :type: Optional[str]
      :value: None

      A template overriding the default ``<th>`` for the column.

For inbuilt support for other types of columns see the
:ref:`HTMX HowTos`.


.. _django-htmx: https://github.com/adamchainz/django-htmx
.. _argus-server: https://github.com/Uninett/Argus
.. _documentation for django-htmx: https://django-htmx.readthedocs.io/en/latest/
.. _daisyUI themes: https://daisyui.com/docs/themes/
.. _list of daisyUI color names: https://daisyui.com/docs/colors/#-2
.. _tailwind-cli-extra: https://github.com/dobicinaitis/tailwind-cli-extra
.. _Tailwind CSS theme customization: https://tailwindcss.com/docs/theme

Custom widget
=============

Argus supports showing an extra widget next to the menubar in the incidents listing. This box can
take the width of 1/3 of the window. You can add the widget by creating a context processor that
injects an ``incidents_extra_widget`` variable that points to an html template::

    def extra_widget(request):
        return {
            "incidents_extra_widget": "path/to/_extra_widget.html",
        }

*note* Don't forget to include the context processor in your settings

You could then create ``path/to/_extra_widget.html`` as following::

    <div id="service-status" class="border border-primary rounded-2xl h-full p-2">
      My custom widget
    </div>


Toast messages
==============

``argus_htmx`` uses the `Django Messages`_ framework to dynamically display notifications toast
messages to the user. Some of these messages stay on screen until the user refreshes, while others
automatically close (disappear) after a certain time. This can be customized by modifying or
overriding the ``NOTIFICATION_TOAST_AUTOCLOSE_SECONDS`` setting. The default value for this setting
is::

  NOTIFICATION_TOAST_AUTOCLOSE_SECONDS = {
      "success": 10,
      "autoclose": 10,
  }

This means that any message that has either the `tag`_ ``"success"`` or ``"autoclose"`` will
automatically close after 10 seconds. You can update this dictionary with existing tags such as
``"warning"`` or ``"error"``, or make up your own.

.. _Django Messages: https://docs.djangoproject.com/en/5.1/ref/contrib/messages
.. _tag: https://docs.djangoproject.com/en/5.1/ref/contrib/messages/#message-tags
