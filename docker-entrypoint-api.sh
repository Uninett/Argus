#!/bin/bash -xe

cd /argus
python3 -m pip install -e .
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
exec daphne -b 0.0.0.0 -p 8000 argus.ws.asgi:application
