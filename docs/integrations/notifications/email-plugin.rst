argus.notificationprofile.media.email.EmailNotification
=======================================================

This plugin is enabled by default.

This plugin uses the email server settings provided by Django itself to
configure the server.

The settings-field for an email-destination contains an
``email_address``-field. It also contains a read-only ``synced``-field, which
is used for some magic if the User model-instance has its
``email_address``-field set. If the email-address has ``synced`` set to True, that
email-address is read-only as far as the API is concerned, because the address
on the User is synced to that specific destination.

To validate the email address we use Django's own email validator.

Using the email plugin to send notifications to Slack
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Slack has the option to send an email to a certain email address, which will
then be sent as a Slack message to a channel or conversation.

To use that feature one needs to get the email address for the relevant channel
or conversation by opening the channel/conversation, clicking the channel or
member name(s) in the conversation header and selecting the tab
``Integrations``. Then select ``Send emails to this channel/conversation.``
and ``Get Email Address.``

If the ability of creating this email address is disabled, please contact an
owner or admin of the Slack workspace.

This email can be copied and a destination with that email address can be
created in Argus and added to notification profiles.

More information about this can be found on the
`Slack help website <https://slack.com/help/articles/206819278-Send-emails-to-Slack#h_01F4WDZG8RTCTNAMR4KJ7D419V>`_.
