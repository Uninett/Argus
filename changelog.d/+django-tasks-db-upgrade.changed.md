We now explicitly depend on "django-tasks" since how "django-tasks-db" depends
on "django-tasks" has changed. We cannot do it the new way, by depending on
"django-tasks-db[compat]", since that conflicts with Django 6.1, which we still
want to be able to test on.
