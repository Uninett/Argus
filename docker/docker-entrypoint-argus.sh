#!/bin/bash -e

django-admin collectstatic --noinput
django-admin migrate --noinput
exec gunicorn \
     argus.site.wsgi:application \
     --forwarded-allow-ips="*" \
     --access-logfile - \
     -b 0.0.0.0:$PORT \
     $@
