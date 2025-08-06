=============================
Howtos and tips for using git
=============================

Set name and email address to use as "Author" or "Committer" for a commit
=========================================================================

This can be set per box you use ``git`` on, or per repo.

If you always want to use the same name and address for all code you commit,
use::

    git config set --global user.name` "YOUR NAME"
    git config set --global user.email "YOUR@EMAIL"

If you don't set ``user.name`` on Linux/\*nix, your username might be used.

If you want to set it per repo, enter the root of the repo and run the command
without the ``--global`` flag::

    git config set user.name` "YOUR NAME"
    git config set user.email "YOUR@EMAIL"

You might want to set the same address for GitHub too, see
:ref:`setting-email-addresses-in-GitHub`.

Merge several names and email address into one with the mailmap file
====================================================================

Sometimes we end up commiting from several different places, with several
different names and email addresses, which makes things look a bit messy.
People also sometimes change their names and email addresses.

While it is possible to change the names and addresses already used for commits
after the fact, the mess can be hidden via a ``.mailmap`` file.

See :ref:`maintaining-mailmap` for how to do this.
