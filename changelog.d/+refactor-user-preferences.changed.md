User preferences were refactored. This is to increase consistency, cut down on
copypasta, and eventually use Django forms on the user preference page, but
more importantly: Django settings are no longer read on import. Turns out,
preferences that depend on Django settings *sometimes* read the settings too
soon, before the settings-file was complete, and therefore getting the wrong or
no setting.
