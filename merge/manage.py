#! /usr/bin/env python3

import django

from django.conf import settings
from django.core.management import call_command

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=(
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "argus.auth",
        "argus.incident",
        "argus.notificationprofile",
        "argus_htmx",
    ),
    MEDIA_PLUGINS=(),
)

django.setup()
call_command("makemigrations", "argus_htmx")
