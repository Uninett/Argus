from django.db import models
from django import forms

from argus.auth.models import Preferences, PreferencesManager


class MagicNumberForm(forms.Form):
    magic_number = forms.IntegerField()


class MyPreferencesManager(PreferencesManager):
    def get_queryset(self):
        return super().get_queryset().filter(namespace=MyPreferences._namespace)

    def create(self, **kwargs):
        kwargs["namespace"] = MyPreferences._namespace
        return super().create(**kwargs)


class MyPreferences(Preferences):
    _namespace = "mypref"
    FORMS = {
        "magic_number": MagicNumberForm,
    }

    class Meta:
        proxy = True
        app_label = "auth"  # not needed outside tests

    objects = MyPreferencesManager()


class MyOtherPreferencesManager(PreferencesManager):
    def get_queryset(self):
        return super().get_queryset().filter(namespace=MyOtherPreferences._namespace)

    def create(self, **kwargs):
        kwargs["namespace"] = MyOtherPreferences._namespace
        return super().create(**kwargs)


class MyOtherPreferences(Preferences):
    _namespace = "myotherpref"
    FORMS = {
        "magic_number": MagicNumberForm,
    }

    class Meta:
        proxy = True
        app_label = "auth"  # not needed outside tests

    objects = MyOtherPreferencesManager()

    def get_context(self):
        context = super().get_context()
        context["jazzpunk"] = "For Great Justice!"
        return context

    def get_foobar_context(self):
        return {"foobar": "xux"}
