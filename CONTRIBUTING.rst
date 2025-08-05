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

Nuts and bolts
==============

* We use pre-commit for linting. We lint the same stuff in CI so make sure your
  stuff is linted before you ask for a review.
* Add yourself to the bottom of the CONTRIBUTORS.md-file if this is your first
  patch.
* We use a template for the message in PRs, it's good enough that we use it
  ourselves. It helps us review the code faster!

  * If there are visible changes to the frontend, add screenshots of before and
    after.

* See the docs for

  * How to write a changelog, and when `(local copy) <./docs/development/howtos/changelog-entry.html>`_, `RTD <https://argus-server.readthedocs.io/en/latest/development/howtos/changelog-entry.html>`_
  * What we want to see in a commit message `(local copy) <./docs/development/howtos/commit-messages.html>`_, `RTD <https://argus-server.readthedocs.io/en/latest/development/howtos/commit-messages.html>`_
