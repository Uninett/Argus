========================
How to vendor a git repo
========================

By "vendoring a repo" we mean to include the source code and history of one git
repo into another, already existing, git repo. Following this how to will give
you one repo with an extra root.

The TARGET repo is the the repo we want to end up with while the ORIGIN
repo is the one we want to merge in (our terms). In this case, we wish to merge
the "main" branch of ORIGIN into the "master" branch of TARGET. (It is easier
to keep track if the branches have different names.)

This how-to assumes that ORIGIN and TARGET has no shared history, as is
the case if ORIGIN is a standalone library or django app.

Prep the ORIGIN repo
====================

1. Be placed somewhere there is no git repo
2. Clone the ORIGIN repo locally::

        git clone ORIGIN-clone path/to/ORIGIN

3. ``cd`` into ORIGIN-clone
4. Make sure you are on "main" branch of ORIGIN-clone
5. Move every single file tracked by git (and not ignored by ``.gitignore``) in
   ORIGIN to a new directory that does not exist on TARGET, we'll standardize
   on ``merge/`` here::

        mkdir merge
        git mv -k * merge/

   Without the ``-k``-flag, ``git mv`` would error out with ``fatal: can not move
   directory into itself, source=merge, destination=merge/merge`` and refuse to
   do anything.

   Finally move the hidden files (filenames that start with ".")::

        git mv -k .* merge/

   Everything should now be in ``merge/`` except for the magic directory
   ``.git/``, any files hidden by ``.gitignore``, and any untracked files. This
   is as it should be.

6. Commit::

        git commit -m 'Move repo contents into subdirectory'

7. Add the TARGET repo as a remote to the ORIGIN-clone::

        git remote add TARGET path/to/TARGET

8. Fetch the TARGET repo into the ORIGIN-clone repo::

        git fetch TARGET

9. Merge ORIGIN-clone's "main" into feceiving's "master"::

        git merge --allow-unrelated-histories TARGET/master

   Note the ``--allow-unrelated-histories``-flag.

10. Push the "master"/"main" of the ORIGIN-clone to a temporary branch on
    TARGET::

        git push -u TARGET merge-ORIGIN

You're finished with the ORIGIN-clone. You may remove it if you like.

Fix up the TARGET repo
======================

1. Switch to a local clone of the TARGET repo
2. Checkout and pull the temporary branch::

        git checkout -b merge-ORIGIN
        git pull
3. You can either merge to "master" now (recommended) or start a new branch off
   merge-ORIGIN for the fixing-up. The goal is to have two different branches:
   one that is a clean copy of ORIGIN's history, one that does all the fixing.
   This makes the latter easy to review and safer to do in general.
4. Whether you merged to "master" or not, start a new branch for the fixing::

        git switch -c move-ORIGIN-files-to-correct-location

5. Do all the moving. Remember that ORIGIN's code might have additional stuff
   in it's ``.gitignore`` and other files (inside ``merge/``) that needs
   to be *added* to the corresponding files of TARGET. Make one commit for
   all files that can be moved without changes and then commit each time you
   need to merge in new stuff. If you need to update import paths or file paths
   in either, they also get a commit each, per path. So: if ORIGIN's module
   name is "my_fine_app" and it will be moved to TARGET's file hierarchy as
   "src/argus/my_fine_app" and module hierarchy as "argus.my_fine_app", make
   one commit for all the file path changes and another for all the "import"
   changes.
6. Push move-ORIGIN-files-to-correct-location upstream so others can have a look::

        git push -u move-ORIGIN-files-to-correct-location

7. When done and tests are green, merge/rebase/squash to "master" (you can do
   this via github).

Done!

If ORIGIN is to cease to exist as a repo, move its open issues to TARGET's
issue tracker.

Transferring Github issues
==========================

It is easy to transfer issues between Github repos, though only one at a time.
There's a link to transfer issues in the right-hand menu on each issue page. If
the TARGET repo has the labels of the ORIGIN repo, the labels will copy over
just fine too.

Notifications will be sent per issue moved so if many are moved at a time give
a heads up to the team: they are about to be spammed.


Move Github PR
==============

If you want to move a PR to the TARGET's official Github you first need to move
the branch, then start a new PR with the same name at TARGET, then link back to
the ORIGIN repo from the new PR. Now you can close the PR in ORIGIN.

Move other branches from ORIGIN to TARGET
=========================================

Prep code in ORIGIN
-------------------

In your local copy of ORIGIN (or a new clone) make a branch off "main" called rename::

        git switch -c rename

Move the code of "main" (just the code) to the paths that are correct for
TARGET. Feel free to also update import paths and template paths in this
code. Commit the changes to the ``rename`` branch.

If the code is going into a new subdirectory, make sure the parent directory is
empty. If necessary ``git rm`` the ``__init__.py`` file or any others.

Setup the remote in the ORIGIN repo
-----------------------------------

1. Add the TARGET repo as a remote::

        git remote add TARGET url/to/TARGET

2. Fetch the branches on argus::

        git fetch TARGET

3. Checkout "master"::

        git switch master

Move the actual branch
----------------------

First move your branch onto the ``rename`` branch.

Do ``git mv old new`` or ``git rebase rename mybranch`` or use a graphical
client to cherry-pick one by one onto "main", or copy the files to the correct
place and add+commit them as new. It is enough to just move the files.
Correcting import paths and file include paths can be done *after* the move, in
the new repo, with a new commit.

This way, you can deal with file renaming conflicts once, and content change
conflicts once.

Now you're ready for the move.

1. Make a temporary branch name for the branch you want to move, at its head::

        git switch mybranch
        git switch -c fvgyhj

2. If it's only a single commit you can cherry-pick it. Move the real name to
   the "master" then cherry-pick::

        git branch -f mybranch master
        git switch mybranch
        git cherry-pick fvgyhj

   If not, a rebase can do it for you. If you didn't do step 1 correctly there
   will be more conflicts than necessary!

   How to rebase (assumes ``mybranch`` is rebased on ``rename``)::

        git rebase --onto master rename mybranch

   You can now remove the temporary branch::

        git branch -d fvgyhj

3. Push the branch to the new remote::

        git switch mybranch
        git push TARGET

Make a new PR
-------------

1. Make the PR in TARGET's repo and pull the branch in your local copy of
   that repo.

2. Do any internal changes to the actual code in the new repo if you didn't do
   that as a part of the branch prep.

Done!
