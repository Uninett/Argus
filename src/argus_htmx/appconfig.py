from argus.site.settings._serializers import ListAppSetting


__all__ = ["APP_SETTINGS"]

_app_settings = [
    {
        "settings": {
            "LOGIN_URL": "/accounts/login/",
            "LOGOUT_URL": "/accounts/logout/",
            "LOGIN_REDIRECT_URL": "/incidents/",
            "LOGOUT_REDIRECT_URL": "/incidents/",
            "PUBLIC_URLS": [
                "/accounts/login/",
                "/api/",
                "/oidc/",
            ],
        },
    },
    {
        "app_name": "argus_htmx",
        "urls": {
            "path": "",
            "urlpatterns_module": "argus_htmx.urls",
        },
        "context_processors": [
            "argus_htmx.context_processors.theme_via_session",
            "argus_htmx.context_processors.datetime_format_via_session",
        ],
        "middleware": {
            "argus_htmx.middleware.LoginRequiredMiddleware": "end",
        },
    },
    {
        "app_name": "django_htmx",
        "middleware": {
            "django_htmx.middleware.HtmxMiddleware": "end",
        },
    },
    {
        "app_name": "widget_tweaks",  # indent for readability
    },
]

APP_SETTINGS = ListAppSetting(_app_settings).root
