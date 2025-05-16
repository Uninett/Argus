INSTALLED_APPS = [
    "django_htmx",
    "widget_tweaks",
    "argus.htmx",
    "django.forms",
    "fontawesomefree",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party apps
    "corsheaders",
    "social_django",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "django_filters",
    "phonenumber_field",
    "knox",
    # Argus apps
    "argus.auth",
    "argus.incident",
    "argus.filter",
    "argus.notificationprofile",
    "argus.dev",
]

MEDIA_PLUGINS = []
# This is just to get the documentation to work
SECRET_KEY = "secret-secret!"
