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

How to customize the look:

* Override Argus' Tailwind CSS theme defaults and/or choose which daisyUI color
  themes to include. You can do so by updating the default
  :setting:`TAILWIND_THEME_OVERRIDE` and :setting:`DAISYUI_THEMES` settings
  respectively before running a ``tailwind_config`` management command:

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
            "color-scheme": "dark",
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

* Override the default main stylesheet path by setting
  ``ARGUS_STYLESHEET_PATH`` in the environment. The path is under
  ``STATIC_URL``. This depends on the context processor
  ``argus.htmx.context_processors.path_to_stylesheet``.
* Include additional styles/stylesheets using the ``head`` block in your templates.
* Generate a Tailwind config file by running the ``tailwind_config`` management
  command. By default the generated file will be based on
  ``src/argus/htmx/tailwindtheme/tailwind.config.template.js`` and expected
  values will be injected with reasonable defaults.

Incident table column customization
===================================

The :setting:`INCIDENT_TABLE_COLUMNS` setting controls which columns are shown
in the incident table. This setting takes a list of ``str`` or
``argus.htmx.incidents.customization.IncidentTableColumn`` instances. when
given a ``str``, this key must be available in the
``argus.htmx.incidents.customization.BUILTIN_COLUMNS`` dictionary. For
example::

    from argus.htmx.incidents.customization import BUILTIN_COLUMNS, IncidentTableColumn

    INCIDENT_TABLE_COLUMNS = [
        "id",
        "start_time",
        BUILTIN_COLUMNS["description"], # equivalent to just "description"
        IncidentTableColumn( # a new column definition
            name="name",
            label="Custom",
            cell_template="/path/to/template.html",  # contents of cell
        ),

    ]


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

      Replacing the default with
      ``htmx/incident/_incident_table_cell_wrapper_link_to_details.html`` will
      result in the ``cell_template`` being wrapped in a link (``<a>``) to the
      details page.

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
--------------

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
