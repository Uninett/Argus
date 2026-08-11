============
CONTRIBUTING
============

Issues are very welcome! If we tag it "wontfix" we will strive to explain why.

Patches are indeed also welcome, in prioritized order:

* Patches for existing issues
* Bugfixes
* More tests, based on ``unittest`` and ``django.test.TestCase`` please
* More integrations (glue services, ticket plugins, notification destinations,
  API clients, especially in other languages..)

  * For integrations in Python "all" (ha!) you need is a package on PyPI and
    a patch with updated info about your integration for the docs. We'll check
    that the package installs and do a quick security check.
  * For integrations in other languages you just need a patch with updated info
    about your integration for the docs.

* Docs fixes
* Fixes that makes the generated OpenAPI better
* Handy tricks in the admin as well as management commands

We're not so keen on:

* Changes to the database schema that can not be considered a bugfix. There
  will be discussions and gnashing of teeth!
* Changes to the stable API
* Lots of information about the world being stored in the same database as
  Argus. Argus isn't an inventory manager for instance. If you need that, build
  something on top of Argus instead, using Argus as a dependency.

Non-negotiable nitpicky stuff
=============================

* Use the PR template when making PRs. We use it ourselves, it is very useful
  for us. It helps us review the code faster, and it helps us when making a new
  release.

  * If there are visible changes to the frontend, add screenshots of before and
    after.

* What we want the commit messages to look like is not a suggestion. See `Howto: Write a good commit message (local copy) <./docs/development/howtos/commit-messages.rst>`_, `Howto: Write a good commit message (on read the docs) <https://argus-server.readthedocs.io/en/latest/development/howtos/commit-messages.html>`_

  Keep crap out of the first line. We won't automatically drop your stuff if
  the first line is slightly longer than 50 characters because that can be
  really hard and we sometimes fail to keep it that short ourselves, but *try*.

Nuts and bolts
==============

* Please set your name and email address in ``git`` and GitHub before your
  first commit if you haven't already:

  * How to set name and email address in git `(local copy) <./docs/development/howtos/howtos-for-git.rst>`_, `RTD <https://argus-server.readthedocs.io/en/latest/development/howtos/howtos-for-git.html>`_
  * How to set email address in GitHub `(local copy) <./docs/development/howtos/howtos-for-github.rst>`_, `RTD <https://argus-server.readthedocs.io/en/latest/development/howtos/howtos-for-github.html>`_

* We use pre-commit for linting. We lint the same stuff in CI so make sure your
  stuff is linted before you ask for a review.
* Add yourself to the bottom of the CONTRIBUTORS.md-file if this is your first
  patch.
* See the docs for

  * How to write a changelog, and when `(local copy) <./docs/development/howtos/changelog-entry.rst>`_, `RTD <https://argus-server.readthedocs.io/en/latest/development/howtos/changelog-entry.html>`_

Contributor License Agreement
=============================

To contribute code to Argus, you need to sign our contributor license
agreement, based on The Free Software Foundation's `Fiduciary License
Agreement 2.0 <https://fsfe.org/activities/ftf/fla.en.html>`_.

We use `CLA assistant`_ to streamline the process. When you create a pull
request against the Argus repository and have not previously signed our
agreement, the assistant will automatically post a comment on your pull
request with instructions on how to sign it digitally using your GitHub
account.

`The full agreement text can be read at the CLA Assistant site.
<https://cla-assistant.io/Uninett/Argus>`_

.. _CLA assistant: https://cla-assistant.io/
