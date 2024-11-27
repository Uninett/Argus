====================
How to vendor a repo
====================

By "vendoring a repo" we mean to include the source code of a repo into an
existing repo. Following this how to will give you one repo with an extra root.

The "receiving" repo is the the repo we want to end up with while the "giving"
repo is the one we want to merge in (our terms). In this case, we wish to merge
the "main" branch of giving into the master" branch of receiving. (It is easier
to keep track if they have different names.)

This how to assumes that "giving" and "receiving" has no shared history,as is
the case if "giving" is a standalone library or django app.

Prep the giving repo
--------------------

1. Be placed somewhere there is no git repo
2. Clone the giving repo locally::

        git clone giving-clone path/to/giving

3. cd into giving-clone
4. Make sure you are on "main" branch of giving-clone
5. Move every single file found by .gitignore in giving to a new directory that
   does not exist on receiving, we'll standardize on ``merge/`` here::

        mkdir merge
        git mv [A-Za-ln-z]* merge/

   We cannot move "merge/" itself, so any files and directories that start with
   "m" needs to have their own ``git mv``-line, like ``manage.py``::

        git mv manage.py merge/

   Trying to move ".git/" will also fail so we need multiple ``git mv`` for
   hidden files as well::

        git mv .[A-Za-fh-z]* merge/
        git mv .git[a-z]* merge/
        git mv .git-[a-z]* merge/

6. Commit::

        git commit -m 'Move repo contents into subdirectory'

7. Add the receiving repo as a remote to the giving-clone::

        git remote add receiving path/to/receiving

8. Fetch the receiving repo into the giving-clone repo::

        git fetch receiving

9. Merge giving-clone's "main" into feceiving's "master"::

        git merge --allow-unrelated-histories receiving/master

10. Push the master/main of the giving-clone to a temporary branch on receiving::

        git push -u receiving merge-giving

You're finished with the giving-clone. You may remove it if you like.

Fix up the receiving repo
-------------------------

1. Switch to a local clone of the receiving repo
2. Checkout and pull the temporary branch::

        git checkout -b merge-giving
        git pull
3. You can either merge to master now (recommended) or start a new branch off
   merge-giving for the fixing-up. The goal is to have two different branches:
   one that is a clean copy of giving's history, one that does all the fixing.
   This makes the latter easy to review and safer to do in general.
4. Whether you merged to master or not, start a new branch for the fixing::

        git switch -c move-giving-files-to-correct-location

5. Do all the moving. Remember that giving's code might have additional stuff
   in it's .gitignore and other files (inside ``merge/``) that needs
   to be *added* to the corresponding files of receiving. Make one commit for
   all files that can be moved without changes and then commit each time you
   need to merge in new stuff. If you need to update import paths or file paths
   in either, they also get a commit each, per path. So: if giving's module
   name is "my_fine_app" and it will be moved to receiving's file hierarchy as
   "src/argus/my_fine_app" and module hierarchy as "argus.my_fine_app", make
   one commit for all the file path cahnges and another for all the "import"
   changes.
6. Push move-giving-files-to-correct-location upstream so others can have a look::

        git push -u move-giving-files-to-correct-location

7. When done and tests are green, merge/rebase/squash to master (you can do
   this via github).

Done!

If giving is to cease to exist as a repo, move open issues to receiving's repo.
That will not be detailed here.

Move other branches from giving to receiving
--------------------------------------------

TBD.
