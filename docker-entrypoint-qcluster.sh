#!/bin/bash -xe

cd /argus
python3 -m pip install -e .
exec python3 manage.py qcluster
