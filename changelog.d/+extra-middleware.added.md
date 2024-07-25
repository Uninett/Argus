`OVERRIDING_APPS` and `EXTRA_APPS` now supports changing the
MIDDLEWARE-setting. The key is "middleware" and the value is a dictionary of
the dotted path of the middleware as the key, and an action as the value.
Currently only the actions "start" and "end" is supported, putting the
middleware at either the start of the list or the end, depending.
