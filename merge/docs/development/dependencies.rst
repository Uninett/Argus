Upgrading HTMX to a new version
===============================

To upgrade the HTMX to a new version, follow these steps:

1. **Backup Current File**:
   Ensure you have a backup of the current `htmx-*.min.js` file located in the `static` directory.

2. **Download the Latest Version**:
   Obtain the latest version of minified HTMX from the `UNPKG`_, for example:
   `https://unpkg.com/htmx.org@2.0.2/dist/htmx.min.js`

3. **Replace Old File**:
   Replace the old HTMX file in your project with the new file from the latest version. This involves updating the `htmx-*.min.js` file in the `static` directory. Make sure to replace the `*` in the file name with the new version number.

4. **Update References**:
   Ensure that all references to HTMX in your project point to the new version. This includes updating the script tag in ``htmx_base.html``::

   <-- HTMX -->
   <script src="{% static "new-htmx-filename.js" %}"></script>


Upgrading Hyperscript to a new version
======================================

To upgrade Hyperscript to a new version, use the same steps as for upgrading HTMX but for the
latest version of Hyperscript on `UNPKG`_, for example:
`https://unpkg.com/hyperscript.org@0.9.13/dist/_hyperscript.min.js`

.. _UNPKG: https://unpkg.com
