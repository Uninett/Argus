#!/bin/bash -xe

cd /argus
git config --global --add safe.directory /argus
python3 -m pip install -e .
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
exec gunicorn -b 0.0.0.0 -p 8000 argus.site.wsgi:application
