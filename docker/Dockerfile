# Defines a production image for the Argus API server
# Needs the repository root directory as its context
FROM python:3.9
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends tini build-essential

# Install some dev requirements that aren't part of the minimal dependencies:
RUN pip install psycopg2-binary django-extensions python-dotenv gunicorn 'uvicorn[standard]'

COPY . /src
RUN pip install /src && rm -rf /src

# Install API backend settings suitable for Docker deployment
RUN mkdir /extrapython
COPY docker/dockersettings.py /extrapython/
ENV PYTHONPATH=/extrapython
ENV DJANGO_SETTINGS_MODULE=dockersettings

ENV PORT=8000
EXPOSE 8000
COPY docker/docker-entrypoint.sh /api-entrypoint.sh
ENTRYPOINT ["/usr/bin/tini", "-v", "--", "/api-entrypoint.sh"]
