# This Dockerfile is designed to run a development environment for Argus,
# with the Argus source code tree mounted at /argus
#
FROM python:3.13-trixie
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends tini \
    build-essential libpq-dev libffi-dev libssl-dev git
RUN mkdir -p /argus
COPY requirements.txt /argus
COPY requirements/*.txt /argus/requirements/

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /argus
RUN pip install gunicorn -r requirements.txt -r /argus/requirements/dev.txt

ENV PYTHONPATH=/argus/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "-v", "--"]
CMD ["/argus/docker-entrypoint.sh"]
