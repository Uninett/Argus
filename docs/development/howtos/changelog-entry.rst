==============================
Howto: Write a changelog entry
==============================

When creating a PR that somehow changes how a user will experience Argus you must add a
changelog entry in form of a file. This file (also called a news fragment) is at the
time of a release used by `towncrier`_ to generate the changelog. This file needs to
be added to the folder ``changelog.d/``.

The name of the file consists of three parts separated by a period:
1. The identifier: either the issue number (in case the pull request fixes that issue)
or the pull request number. If we don't want to add a link to the resulting changelog
entry then a ``+`` followed by a unique short description, for instance the name of the
branch.
2. The type of the change: we use ``security``, ``removed``, ``deprecated``, ``added``,
``changed`` and ``fixed``.
3. The file suffix, e.g. ``.md``, towncrier does not care which suffix a fragment has.

So an example for a file name related to an issue/pull request would be ``214.added.md``
or for a file without corresponding issue ``+fixed-pagination-bug.fixed.md``.

This file can either be created manually with a file name as specified above and the
changelog text as content or one can use towncrier to create such a file as following:

.. code:: console

   $ towncrier create -c "Changelog content" 214.added.md

When opening a pull request there will be a check to make sure that a news fragment is
added and it will fail if it is missing.

.. _towncrier: https://towncrier.readthedocs.io
