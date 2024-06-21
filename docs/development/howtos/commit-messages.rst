==================================
Howto: Write a good commit message
==================================

First line
==========

The first line of the commit message should strive to be 50 characters or less.
It is always better to spend those characters on a good, short summary of what
the commit does. Avoid prefixes like "feat:" or adding issue numbers/pull
request numbers.

Complete the sentence "Merging this commit will…".

Examples:

* Fix typo
* Remove unused cruft
* Avoid triggering a race condition
* Fix off-by-one error
* Optimize database lookup
* Prevent a 500 server error on Feb 29
* Properly handle FooError on logout
* Split up test file
* Move Bar to separate file

Feel free to use a thesaurus to find a good verb.

More info
=========

If there is more to add, have a blank line after the first line then describe
away. Issue numbers, pull request numbers, links to more info can all go here.

Explanations as to what is actually going on are especially welcome.

If this a pull request with a good and beefy explanation, copy the explanation
to the body of the commit so that the explanation stays with the code.

Collaborators
=============

If you worked together with someone else on a commit, add them to the bottom
like this::

    ---------

    Co-authored-by: N N <nomen.nescio@example.org>

(Github might do this for you.)

Squashed commits
================

This repo prefers a linear commit history, so squash early, squash often.

Let the first line describe the set of commits as a whole. Then, after a blank
line, you can list the original messages, just remember to remove any "Fix
typo" (if it fixes a typo introduced earlier in this set of commits), "fixup",
"whoops", random letters knuckle-rolled in frustration and similar.

If the same message occurs more than once, keep only one. Remove it entirely
if it is a frustration-commit.

If one commit adds something and a later commit in the same set removes it,
please delete both messages.

After the first line and before the list of commits included you can add more
info just like with a non-squashed commit: links, issue numbers, explanations
etc.

If there are any "Co-authored-by"-blocks, collect them all at the bottom like
so::

    ---------

    Co-authored-by: Huey Duck <huey@duck.net>
    Co-authored-by: Dewey Duck <dewey@duck.net>
    Co-authored-by: Louie Duck <louie@duck.net>
    Co-authored-by: N N <nomen.nescio@example.org>
