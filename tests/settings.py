SECRET_KEY = "fake-key"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    #     "argus.auth",
    "tests",
]
ROOT_URLCONF = "tests.urls"
