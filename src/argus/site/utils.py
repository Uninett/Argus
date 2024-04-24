# nothing that imports models here!

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
