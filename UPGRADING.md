# UPGRADING

## 1.0

For version 1, we reset all the migrations for Argus's own apps:

* argus_notificationprofile
* argus_incident
* argus_auth

Please drop the database. This is the only time we're doing this.

If you do not have access to drop and recreate the database, you can start the
(postgres) database shell like so: `$ python manage.py dbshell` and delete all
tables like so:

```
DROP OWNED BY argus;
```

Then recreate the tables with:

```
$ python manage.py migrate
```
