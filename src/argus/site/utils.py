# nothing that imports models here!
from copy import deepcopy

from django.urls import include, path


def get_app_names(app_settings):
    return [app.app_name for app in app_settings if app.app_name]


def get_urlpatterns(app_settings):
    if not app_settings:
        return []
    urlpatterns = []
    for app in app_settings:
        if not app.urls:
            continue
        if app.urls.namespace:
            include_item = app.urls.urlpatterns_module, app.urls.namespace
        else:
            include_item = app.urls.urlpatterns_module
        # fmt: off
        urlpatterns.append(
            path(app.urls.path, include(include_item))
        )
        # fmt: on
    return urlpatterns


def update_context_processors_list(templates_setting, app_settings):
    if not templates_setting:
        return templates_setting
    safety_copy = deepcopy(templates_setting)
    correct_engine = None
    for engine in safety_copy:
        if engine["BACKEND"] == "django.template.backends.django.DjangoTemplates":
            correct_engine = engine
            break
    else:
        return templates_setting
    for app in app_settings:
        if not app.context_processors:
            continue
        correct_engine["OPTIONS"]["context_processors"].extend(app.context_processors)
    return safety_copy


def update_middleware_list(middleware_setting, app_settings):
    if not middleware_setting:
        return middleware_setting
    safety_copy = middleware_setting[:]
    start_list = []
    end_list = []
    for app in app_settings:
        if not app.middleware:
            continue
        for middleware, action in app.middleware.items():
            if action == "start":
                start_list.append(middleware)
            else:
                end_list.append(middleware)
    safety_copy = start_list + safety_copy + end_list
    return safety_copy


def get_settings(app_settings):
    settings = {}
    for app in app_settings:
        if not getattr(app, "settings", None):
            continue
        settings.update(app.settings)
    return settings


def update_settings(current_settings, app_settings, override=False):
    if not app_settings:
        return
    TEMPLATES = current_settings["TEMPLATES"]
    INSTALLED_APPS = current_settings["INSTALLED_APPS"]
    MIDDLEWARE = current_settings["MIDDLEWARE"]

    _app_names = get_app_names(app_settings)
    if override:
        INSTALLED_APPS = _app_names + INSTALLED_APPS
    else:
        INSTALLED_APPS += _app_names
    current_settings["INSTALLED_APPS"] = INSTALLED_APPS
    TEMPLATES = update_context_processors_list(TEMPLATES, app_settings)
    current_settings["TEMPLATES"] = TEMPLATES
    MIDDLEWARE = update_middleware_list(MIDDLEWARE, app_settings)
    current_settings["MIDDLEWARE"] = MIDDLEWARE

    for setting, value in get_settings(app_settings).items():
        current_settings[setting] = value
