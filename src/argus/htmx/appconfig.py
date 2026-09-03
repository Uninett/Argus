from argus.site.settings._serializers import ListAppSetting


__all__ = ["APP_SETTINGS"]

# Order matters! Later entries can use stuff in earlier entries
_app_settings = [
    {
        "settings": {
            "LOGIN_URL": "htmx:login",
            "LOGOUT_URL": "htmx:logout",
            "LOGIN_REDIRECT_URL": "htmx:incident-list",
            "LOGOUT_REDIRECT_URL": "htmx:incident-list",
            "PUBLIC_URLS": [
                "htmx:login",
                "/api/",
                "/oidc/",
            ],
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
    {
        "app_name": "argus.htmx",
        "urls": {
            "path": "",
            "urlpatterns_module": "argus.htmx.urls",
        },
        "context_processors": [
            "argus.auth.context_processors.preferences",
            "argus.htmx.context_processors.static_paths",
            "argus.htmx.context_processors.banner_message",
        ],
        "middleware": {
            "argus.htmx.middleware.LoginRequiredMiddleware": "end",
            "argus.htmx.middleware.HtmxMessageMiddleware": "end",
        },
    },
    {
        "app_name": "django.forms",
        "settings": {"FORM_RENDERER": "django.forms.renderers.TemplatesSetting"},
    },
    {
        "app_name": "fontawesomefree",
    },
]

APP_SETTINGS = ListAppSetting(_app_settings).root
