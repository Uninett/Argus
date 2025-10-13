from argus.site.settings._serializers import ListAppSetting
from argus.util.app_utils import is_using_psa


__all__ = ["APP_SETTINGS"]

# Order matters! Later entries can use stuff in earlier entries
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

if is_using_psa():
    _app_settings += [
        {
            "app_name": "social_django",
            "middleware": {
                "social_django.middleware.SocialAuthExceptionMiddleware": "end",
            },
            "context_processors": [
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
            "urls": {
                "path": "oidc/",
                "urlpatterns_module": "social_django.urls",
                "namespace": "social",
            },
        }
    ]


APP_SETTINGS = ListAppSetting(_app_settings).root
