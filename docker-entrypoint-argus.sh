#!/bin/bash -xe

cd /argus
git config --global --add safe.directory /argus
python3 -m pip install -e .
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput

# Stop password from being printed in logs
set +x
if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
     if [ -n "$ADMIN_EMAIL" ]; then
         python3 manage.py initial_setup -u $ADMIN_USERNAME -p $ADMIN_PASSWORD -e $ADMIN_EMAIL
     else
          python3 manage.py initial_setup -u $ADMIN_USERNAME -p $ADMIN_PASSWORD
     fi
fi
set -x

exec gunicorn -b 0.0.0.0 -p 8000 argus.site.wsgi:application
