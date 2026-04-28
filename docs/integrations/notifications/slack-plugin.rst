Slack notifications using incoming webhooks
===========================================

| Class: ``argus.notificationprofile.media.slack.SlackNotification``

This plugin is **not** enabled by default.

This is a minimal plugin built on Apprise. All you need to get started is an incoming webhook connected to your Slack app.
For instructions on how to set this up, see `Sending messages using incoming webhooks
<https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks>`__.

The settings-field for a slack-destination contains a value that looks like a ``URL``,
either being a slack webhook or an apprise URL.
