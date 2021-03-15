# set tw: 72

=================
Release checklist
=================

#. Ensure we're on the correct branch to be released, and that HEAD is the
   commit we want to tag with the new version:

    .. code formatting:: console

        $ git log --oneline  --decorate HEAD~5..HEAD

#. Check that there are no files that have not been commited:

    .. code formatting:: console

        $ git status

#. Run the tests one last time.

    .. code formatting:: console

        $ tox

#. Tag the correct commit with an annotated tag. The format of the tag itself
   is vX.Y.Z where X, Y and Z are integers. The annotation should be a very
   brief summary of the most important changes.

    .. code formatting:: console

        $ git tag -m 'Post release bugfixes' v1.0.1

#. Push the tag (given that `origin` is the correct remote):

    .. code formatting:: console

        $ git push origin v1.0.1

#. Create the python wheel:

    .. code formatting:: console

        python3 setup.py bdist_wheel

   This will create a wheel in the ``dist/`` directory.

#. Do a quick manual check of the contents of the wheel: Check that the correct
   version is in the filename (if not, you might have forgotten to tag, or the
   git index is dirty):

    .. code formatting:: console

        $ ls dist/

   Then check the contents with any tool that can analyze
   a zip-file, for instance ``zipinfo``. Check that no unwanted files are
   included, like editor swap files, ``.pyc`` files, or ``__pycache__``
   directories:

    .. code formatting:: console

        $ zipinfo dist/FILENAME

#. Upload the wheel at `PyPI <https://pypi.org/>`_, for instance with
   `twine <https://twine.readthedocs.io/>`_:

    .. code formatting:: console

        $ twine upload dist/\*.whl

#. Turn the tag into a release on Github. (On the "Code" tab, find the column
   to the right of the list of files and scroll until you find "Releases".
   Click on "Releases". To the right, find the button "Draft new release".
   Click. Type in the tag in the box that says "Tag version" left of the '@',
   and copy the tag where it says "Release title". Then click the "Publish
   release"-button.)
