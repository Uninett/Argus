Added a new log level: TRACE, for stuff even less important than DEBUG. In the
process, moved logging helpers to a dedicated home in anticipation of
supporting better logging in production.

This new level is really not a good match for use in production, expect a lot
of noise. See NOTES for configuration.

NOTES:


`TRACE` is not an unusal level to have, so if you set the root logger to
`TRACE` you might get a lot of noise from dependencies. We therefore recommend
that you never set the root logger to `TRACE` but instead set it on specific
subloggers when you need higher detail. `TRACE` is currently only used in the
`argus.htmx` app for now.

If treating argus as a library, you will need to make sure that
`argus.logging.utils.setup_logging` has been run for this new level to work.
`argus.settings.base` does this automatically.

If you get the exception

> AttributeError: 'Logger' object has no attribute 'trace'

this is caused by `setup_logging()` never having been run. `setup_logging()`
with no parameters is idempotent and thus safe to run multiple times.
