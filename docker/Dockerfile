# Defines a production image for the Argus API server
# with an optional all-plugins target
# Needs the repository root directory as its context:
#
# If you're in the same directory as this Dockerfile try:
#   docker build -f Dockerfile ..
#
# If you're in the repository root try:
#   docker build -f docker/Dockerfile .

# ── build stage ─────────────────────────────────────
# Builds the virtualenv in a throwaway stage. git is required here because the
# Argus version is derived from git metadata by versioningit at install time;
# the C toolchain and -dev headers cover any dependencies without binary
# wheels. None of these build dependencies end up in the runtime image.
FROM python:3.13-slim-trixie AS build
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libffi-dev libssl-dev git \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Runtime dependencies that aren't part of the minimal package dependencies:
RUN pip install "psycopg[binary]" django-extensions python-dotenv gunicorn

COPY . /src
RUN pip install /src

# ── runtime base ────────────────────────────────────
# Slim runtime image that carries over only the virtualenv built above, so
# neither the build toolchain nor the source tree (including its git history)
# bloat the published image.
FROM python:3.13-slim-trixie AS base
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=build $VIRTUAL_ENV $VIRTUAL_ENV

# Make an unprivileged user to run the server
RUN useradd --system argus
# Ensure this user has privileges to collect static resources in /static
RUN mkdir -p /static && chown argus /static
ENV STATIC_ROOT=/static

# Install API backend settings suitable for Docker deployment
RUN mkdir /extrapython
COPY docker/dockersettings.py /extrapython/
ENV PYTHONPATH=/extrapython
ENV DJANGO_SETTINGS_MODULE=dockersettings

ENV PORT=8000
EXPOSE 8000
COPY docker/cmd-argus.sh /cmd-argus.sh
COPY docker/cmd-dbqueue.sh /cmd-dbqueue.sh
USER argus
ENTRYPOINT ["/usr/bin/tini", "-v", "--"]
CMD ["/cmd-argus.sh"]

# ── all-plugins target ──────────────────────────────
# Includes all Sikt-maintained notification and ticket plugins. These are
# pure-Python wheels, so they install on the slim runtime without the build
# toolchain. (If a plugin ever needs compilation, install them in a stage that
# extends `build` instead and copy the resulting venv.)
FROM base AS all-plugins
USER root
COPY --from=build /src/pyproject.toml /tmp/pyproject.toml
RUN pip install --group /tmp/pyproject.toml:all-plugins
USER argus
