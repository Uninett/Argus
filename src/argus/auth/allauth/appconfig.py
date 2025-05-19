from argus.site.settings._serializers import ListAppSetting


# Order matters! Later entries can use stuff in earlier entriesq
__all__ = ["APP_SETTINGS"]

_app_settings = [
    {"app_name": "allauth"},
    {
        "app_name": "allauth.account",
        "middleware": {"allauth.account.middleware.AccountMiddleware": "end"},
        "settings": {"ACCOUNT_MAX_EMAIL_ADDRESSES": 1},
    },
    {
        "app_name": "allauth.mfa",
        "settings": {
            "MFA_ADAPTER": "allauth.mfa.adapter.DefaultMFAAdapter",
            "MFA_TOTP_ISSUER": "Argus",
            "MFA_TOTP_TOLERANCE": 0,
        },
    },
]

APP_SETTINGS = ListAppSetting(_app_settings).root
