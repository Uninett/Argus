..
   set tw: 72

==========================
How To: Make a new release
==========================

This howto uses version number "1.5.1" throughout as an example. Remember to
edit all copy-pastes that have "1.5.1" in them to the correct version number!

Choosing a version number
-------------------------

While we use `SemVer <https://semver.org/>`_, SemVer is open to interpretation
so here is ours.

Increase the middle digit every time when

* there is a change in the database schema that necessitates a migration
  on the production SQL server. (Django also has migrations that do *not*
  necessitate this.)
* there is a change that automatically rewrites the data in the database (aka
  a "data migration")
* there is a change in the REST API that cannot be ignored by clients
  (especially *removed* attributes)
* there is a wonderful new feature that needs to be highlighted
* the deployer needs to do extra steps, like ensuring that a new
  dependency is installed
* there is a bugfix that necessitates some hands-on action from the deployer

Increase the final digit when

* changing documentation
* changing something in CI/CD like updating CI/CD specific dependencies
* adding a bugfix that nobody should notice

Releases that only change the final digit should *never* be mentioned
in :file:`NOTES.md`.

We plan to increase the first digit when dropping a REST API version. We have
not needed to do this yet.

Checklist
---------

#. Ensure you're on the correct branch to be released. Either ``master`` or
   newest stable, which has a name of the form ``stable/1.5.x``. Release from
   the stable branch only under exceptional circumstances. For instance:
   there's a critical bugfix for production and there's a lot of new stuff on
   master that is not ready to go.

#. Check that there are no files that have not been commited:

    .. code:: console

        $ git status

#. Run the tests one last time:

    .. code:: console

        $ tox

#. Check that :file:`CHANGELOG.md` and :file:`NOTES.md` are up to snuff. We use
   :command:`towncrier` to add to the changelog from the files in
   :file:`changelog.d/`.

   Run :code:`towncrier build --version 1.5.1`. This will update
   :file:`CHANGELOG.md` and delete everything in :file:`changelog.d/`.

   Read the new entry in :file:`CHANGELOG.md` and adjust it as necessary for
   better language. Reorder as per the order the commits/pull-requests were
   commited, newest on top. That makes it easier to compare with the ``git log``
   for maximum detail.

   Copy steps that a deployer needs to do to :file:`NOTES.md`, feel free to add
   more detail.

   Use ``git add -u`` to ensure the changes to :file:`changelog.d/` are
   included. Make one standalone commit for this step.

#. Check that HEAD is the commit we want to tag with the new version:

    .. code:: console

        $ git log --oneline  --decorate HEAD~5..HEAD

   This is preferably the commit that adjusted the changelog and notes.

#. Tag the correct commit with an annotated tag. The format of the tag itself
   is ``vX.Y.Z`` where X, Y and Z are integers. Don't forget the ``v``. The
   annotation should be a very brief summary of the most important changes. The
   annotation need not be unique, there just must be *something* to make the
   tag annotated.

    .. code:: console

        $ git tag -m 'Post release bugfixes' v1.5.1

#. Push the tag and changelog commit (given that ``origin`` is the correct
   remote):

    .. code:: console

        $ git push origin

   Note: we bypass pull-requests here.

#. Create a wheel and source tarball:

    .. code:: console

        $ python -m build

   This will create a wheel in the :file:`dist/` directory.

   (You can install ``build`` locally for your user with :command:`pipx` and
   run :command:`pyproject-build` instead, it'll do the same thing.)

#. Do a quick manual check of the contents of the wheel: Check that the
   correct version is in the filename (if not, you might have forgotten
   to tag, or the git index is dirty):

    .. code:: console

        $ ls dist/

   Then check the contents with any tool that can analyze
   a zip-file, for instance ``zipinfo``. Check that no unwanted files are
   included, like editor swap files, ``.pyc`` files, or ``__pycache__``
   directories:

    .. code:: console

        $ zipinfo dist/FILENAME.wheel

#. Upload the wheel at `PyPI <https://pypi.org/>`_, for instance with
   `twine <https://twine.readthedocs.io/>`_:

    .. code:: console

        $ twine upload dist/*.whl

   Use your own user if you've been given access or ask for a token for
   the team-user, see also :file:`~/.pypirc`.

#. Turn the tag into a release on Github:

   #. On the "Code" tab, find the column to the right of the list of
      files and scroll until you find "Releases". Click on
      "Releases".

   #. To the right, find the button "Draft new release". Click.

   #. Type in the tag in the box that says "Tag version" left of the
      '@', in order to select the tag.

   #. Copy the tag and date from the changelog to where it says "Release
      title".

   #. Copy the changelog into the box below, dedent the headers once.

   #. Finally, click the "Publish release"-button. Done!
