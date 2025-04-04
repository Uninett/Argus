# Defines a production image for the Argus API server
# Needs the repository root directory as its context
FROM python:3.12
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends tini build-essential

# Install some dev requirements that aren't part of the minimal dependencies:
RUN pip install psycopg2-binary django-extensions python-dotenv gunicorn 'uvicorn[standard]'

# Make an unprivileged user to run the server
RUN useradd --system argus
# Ensure this user has privileges to collect static resources in /static
RUN mkdir -p /static && chown argus /static
ENV STATIC_ROOT=/static

COPY . /src
RUN pip install '/src[spa]' && rm -rf /src

# Install API backend settings suitable for Docker deployment
RUN mkdir /extrapython
COPY docker/dockersettings.py /extrapython/
ENV PYTHONPATH=/extrapython
ENV DJANGO_SETTINGS_MODULE=dockersettings

ENV PORT=8000
EXPOSE 8000
COPY docker/docker-entrypoint.sh /api-entrypoint.sh
USER argus
ENTRYPOINT ["/usr/bin/tini", "-v", "--", "/api-entrypoint.sh"]
