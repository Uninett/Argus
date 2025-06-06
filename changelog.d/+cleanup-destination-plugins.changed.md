Moved a lot of common infrastructure from our NotificationMedium subclasses to
the parent. This should make it easier to create more media of high quality.
Also, it should make it easier to use the plugins for validating the
settings-file elsewhere than just the API.

This might break 3rd party notification plugins.
