================================
Howtos and tips for using GitHub
================================

.. _setting-email-addresses-in-GitHub:

Set email address used when committing in the web interface
===========================================================

GitHub gives every user a magic no-reply email address of the form
``0000000+username@users.noreply.github.com`` which by default is used as the
"Committer" in a git commit made via the web interface.

If this email address has not been set for the git repo or user on your
development box, the commits you make via CLI and the commits you make via the
web interface will have different email addresses.

You can associate other email addresses with your GitHub account in the `Github
email settings <https://github.com/settings/emails>`_ page and use those when
you commit (also useful if you have changed your email). The one set as primary
is the one that will be shown in the web interface unless you want to use the
magic address GitHub provides for you, then you need to toggle "Keep my email
addresses private" on the same page to "On". You can even prevent commits not
using the magic address from being pushed to GitHub.

See `Setting your commit email address at GitHub<https://docs.github.com/en/account-and-profile/how-tos/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address>`_ for more information.
