# nothing that imports models here!
from copy import deepcopy

from django.conf import settings
from django.urls import include, path


def get_urlpatterns_from_setting(setting):
    if not setting:
        return []
    urlpatterns = []
    for app in setting:
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
