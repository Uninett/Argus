# nothing that imports models here!

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


def update_context_processors_list(new_context_processors):
    setting = getattr(settings, "TEMPLATES", None)
    if not setting:
        return None
    correct_engine = None
    for engine in setting:
        if setting["BACKEND"] == "django.template.backends.django.DjangoTemplates":
            correct_engine = engine
            break
    if not correct_engine:
        return False
    correct_engine["OPTIONS"]["context_processors"].extend(new_context_processors)
    return True
