=======================================
How to use Font Awesome icons
=======================================

The Argus htmx frontend uses the `Font Awesome`_ icon pack for rendering icons. You must install it
as a Django App, which is done automatically by
`applying <https://argus-server.readthedocs.io/en/latest/reference/htmx-frontend.html#configure>`_
the ``argus.htmx.appconfig.APP_SETTINGS``.

You can now add a font-awesome icon by adding an ``<i>`` element::

  <i class="fa-solid fa-magnifying-glass"></i>

To change the icon colour, use the ``text-<color>`` Tailwind classes. Similarly, you can change the
icon size using Tailwind, for example by setting the ``text-sm`` or ``text-lg`` class.


.. _Font Awesome: https://fontawesome.com/
