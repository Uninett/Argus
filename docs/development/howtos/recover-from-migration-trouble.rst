=====================================
Howto: Recover from migration trouble
=====================================

You or somebody else has been working on changing the database schema and now
you get errors when trying to migrate

For instance:
Some migrations have changed names. The file for the original migration is gone
so it can't be undone.

Don't panic!

The easiest is to roll back to the backup of the database (make a script to do
it for you) that you made before you ran the migration.

The second easiest is to start with a fresh database.

The third is to manually undo what the migrations did and fix the
``django_migrations``-table. You'll need to be able to run ``manage.py dbshell``.

How to undo depends on what was done so this howto cannot go into detail. Make
note of which apps were involved, write down their ``app_label``\s.

If the troublesome migration was in, say, ``argus_auth``. Start ``dbshell``, then::

    argus=> SELECT * FROM django_migrations WHERE app = 'argus_auth';
    id |    app     |             name            |            applied
    ---+------------+-----------------------------+-------------------------------
    14 | argus_auth | 0001_initial                | 2024-04-30 11:15:34.488091+02
    19 | argus_auth | 0002_alter_user_first_name  | 2024-04-30 11:15:34.798425+02
    20 | argus_auth | 0003_delete_phonenumber     | 2024-04-30 11:15:34.80969+02
    34 | argus_auth | 0004_evil_migration         | 2024-06-04 12:49:41.035624+01
    35 | argus_auth | 0005_other_migrations       | 2024-06-05 12:52:22.468977+01
    (5 rows)

So we know that "0003_delete_phonenumber" was the last good migration.

Do::

    DELETE FROM django_migrations WHERE app = 'argus_auth' AND id > 20;

This will delete the lines with id 34 and 35 and your migration history should
be in sync with your database.
