.. _howto-override-templates:

====================
Override templates
====================

The Argus htmx templates are locatied in ``src/argus/htmx/templates``. One of the main ways to
customize Argus is by extending and overriding those templates. First of all, make sure that your
app is listed before the ``argus.htmx`` app in your ``INSTALLED_APPS`` so that templates are first
looked up in you app, before looking up the templates in the ``argus.htmx`` app::

  INSTALLED_APPS = [
    "my_app",
    ...,
    "argus.htmx",
    ...,
  ]

Alternatively, you can use the ``OVERRIDING_APPS`` :ref:`setting<site-specific-settings-additional-apps>`
or ``ARGUS_OVERRIDING_APPS`` environment variable.

Now, let's say you have created a page and want to add a link to it in the top header, next to
"Profiles". That section is defined in the ``htmx/base.html`` template in the ``navlinks`` blocks.
To extend that template, create a new file in your own app called ``templates/htmx/base.html`` and
add the following content::

  {% extends "htmx/base.html" %}
  {% block navlinks %}
    {{ block.super }}
      <li>
        <a href="{% url 'my_app:my_page' %}">My Custom Page</a>
      </li>
  {% endblock navlinks %}

Let's break this down in parts:

 * The ``{% extends %}`` tag tells Django to look for a template with that name and base your
   template on that. Crucially, if the template name is the same as the current template, it
   will look for the next template in the app list with that name, so it will not lead to infinite
   recursion
 * the ``{% block %}`` tab tells Django to reimplement a block with that name in the base template
 * ``{{ block.super }}`` renders the original content of that block
 * We then add our own content to the block

The ``htmx/base.html`` template located in ``src/argus/htmx/templates/`` is itself extending the
``htmx_base.html`` template, and you can also extend/override any block defined in that template
but not referenced in the ``htmx/base.html`` template, such as the ``title`` or ``footer`` block.
So we can update our customize ``htmx/base.html`` as following to change the title::

  {% extends "htmx/base.html" %}
  {% block title %}
    <title>My Custom Argus: {{ page_title }}</title>
  {% endblock title %}
  {% block navlinks %}
    {{ block.super }}
      <li>
        <a href="{% url 'my_app:my_page' %}">My Custom Page</a>
      </li>
  {% endblock navlinks %}

Also note that it is not required to use the ``{% extends %}`` tag if you want to completely
override the original template.

For more information, see `Django template tags`_.


Use cases for overriding templates
==================================

Below is a list of templates that you may want to override for your use cases. This is by no means
an extensive list, but can provide entry points or inspiration:

* ``htmx/base.html``: add or remove nav links
* ``htmx/incident/_incident_list_menubar.html``: remove the ``_filter_controls`` widget from the
  filter box. This requires a full template override by copy/pasting the original template and modifying its content
* ``htmx/incident/_incident_list_update_menu.html``: add custom action buttons to the "Update
  Incidents" tab in this incident list
* ``htmx/incident/cells/*.html``: customize how incident list column cells are rendered
* ``htmx/incident/incident_detail.html``: customize the indicent details page
* ``htmx/incident/incident_list.html``: add additional content to the incident list page, outside
  of the table
* ``htmx/incident/responses/_incident_list_refresh.html``: add additional content, such as
  ``hx-swap-oob`` content, to a incident list htmx partial response
* ``htmx/user/_user_menu.html``: add or remove items to the user menu (the menu that appears when
  clicking on the user's initials in the top right)
* ``htmx/user/preferences.html``: add custom preferences to the preferences page
* ``registration/login.html``: show additional information to a user prior to logging in, such as
  a link to a privacy policy or other terms



.. _Django template tags: https://docs.djangoproject.com/en/5.2/ref/templates/builtins/
