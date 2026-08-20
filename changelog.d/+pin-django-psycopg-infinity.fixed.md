Pinned `django-psycopg-infinity` to 0.1.0. Version 0.1.1 changed infinity
timestamps loaded from `timestamp with time zone` columns from local time to
UTC. Since infinity is represented as a wall-clock sentinel rather than a true
instant, the two are not equal, so an incident's `end_time` no longer compared
equal to the infinity constant after being reloaded from the database. Among
other things this made notifications for open incidents render an explicit
far-future timestamp instead of "Still open".
