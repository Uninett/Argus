#!/bin/bash -e

django-admin collectstatic --noinput
django-admin migrate --noinput

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

exec gunicorn \
     argus.site.wsgi:application \
     --forwarded-allow-ips="*" \
     --access-logfile - \
     -b 0.0.0.0:$PORT \
     $@
