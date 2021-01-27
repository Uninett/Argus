# set tw: 72

=================
Release checklist
=================

#. Ensure we're on the correct branch and that HEAD is set correctly.
#. Run the tests one last time.
#. Tag the correct commit with an annotated tag, the format of the tag
   itself is vX.Y.Z where X, Y and Z er integers.
#. Push the tag
#. Run ``python3 setup.py bdist_wheel``. This will create a wheel in the
   ``dist/`` directory.
#. Do a quick manual check of the contents of the wheel: Check that the
   correct version is in the filname (if not, you might have forgotten
   to tag!). Check the contents with any tool that can analyze
   a zip-file, for instance ``zipinfo``. Check that no unwanted files
   are included, like editor swap files, ``.pyc`` files, or
   ``__pycache__`` directories.
#. Upload the wheel at `PyPI <https://pypi.org/>`_, for instance with
   `twine <https://twine.readthedocs.io/>`_:

   .. code formatting:: console

      $ twine upload dist/\*.whl

#. Turn the tag into a release on Github.
