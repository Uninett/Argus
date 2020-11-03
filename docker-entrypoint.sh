#!/bin/bash -xe

cd /argus
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
python3 manage.py initial_setup
python3 manage.py create_fake_incident -b 15
exec gunicorn --forwarded-allow-ips="*" --log-level debug --access-logfile - argus.site.wsgi -b 0.0.0.0:8000
