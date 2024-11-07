from django.db import models
from django import forms

from argus.auth.models import Preferences, preferences_manager_factory


class MagicNumberForm(forms.Form):
    magic_number = forms.IntegerField()


class MyPreferences(Preferences):
    _namespace = "mypref"
    FORMS = {
        "magic_number": MagicNumberForm,
    }
    FIELD_DEFAULTS = {
        "magic_number": 42,
    }

    class Meta:
        proxy = True
        app_label = "auth"  # not needed outside tests

    objects = preferences_manager_factory(_namespace)()


class MyOtherPreferences(Preferences):
    _namespace = "myotherpref"
    FORMS = {
        "magic_number": MagicNumberForm,
    }
    FIELD_DEFAULTS = {
        "magic_number": 5,
    }

    class Meta:
        proxy = True
        app_label = "auth"  # not needed outside tests

    objects = preferences_manager_factory(_namespace)()

    def get_context(self):
        context = super().get_context()
        context["jazzpunk"] = "For Great Justice!"
        return context

    def update_context(self, _):
        return {"foobar": "xux"}
