The settings files have changed, since the HTMx frontend app is now included by
default. The frontend settings has been merged in and no longer need the
settings overriding machinery. It is no longer necessary to install the
frontend with `pip install argus-server[htmx]`, just `pip install argus-server`
will do.
