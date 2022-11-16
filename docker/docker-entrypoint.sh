#!/bin/bash -e

django-admin collectstatic --noinput
django-admin migrate --noinput
exec daphne -b 0.0.0.0 -p $PORT argus.ws.asgi:application
