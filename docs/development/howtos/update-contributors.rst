====================================================
Howto: Maintaining the contributors file and mailmap
====================================================

Maintaining CONTRIBUTORS.md
===========================

``CONTRIBUTORS.md`` contains the official list of contributors to Argus.

It is preferrable that new contributors (both code authors and code committers)
add themselves at the end, but it can also be done after the fact via some
variation of::

    $ git log --all --pretty="%ad %ae %an" --date=iso | sort -u

which outputs full ISO timestamp, email address and name for the commits,
sorted by date, oldest first.

As an example, as of the creation of this howto, the first entry for
"dependabot" is::

    2021-03-22T14:40:04+01:00 49699333+dependabot[bot]@users.noreply.github.com dependabot[bot]

The format for a contributor in the CONTRIBUTORS.md is::

    * [Name of contributor](link to preferred homepage) \<preferred@email.address\>

If there is no preferred homepage the contributor name need not be a link::

    * Name of contributor \<preferred@email.address\>

.. _maintaining-mailmap:

Maintaining .mailmap
====================

``.mailmap`` exists to combine email addresses and contributor names of
contributors that have several. This is useful for ``git blame`` and ``git
log``.

This happens when the contributor commits from several different computers and
tools with different configurations for name and email. Github also gives each
user a github-specific email address that may be used when authoring/committing.

.. tip:: To prevent multiple names and addresses for the same author/committer
    in the first place, make sure to explicitly configure this in every tool
    used to commit.

For readability, we update the `.mailmap`-file manually. The file starts with
a block of preferred names and email addresses in the "canonical" section.

The format is::

    Preferred Name <preferred@email.address>

This is followed by a list of rewrites to map names and email addresses to the
preferred forms in the "rewrites" section. The format is described in
`gitmailmap(5) <https://git-scm.com/docs/gitmailmap>`_.

You can get a list of all used names and email addreses via::

    $ git log --format='%an <%ae>' | sort -u
