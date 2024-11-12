from django import forms

from argus.auth.models import preferences


class MagicNumberForm(forms.Form):
    magic_number = forms.IntegerField()


@preferences(namespace="mypref")
class MyPreferences:
    FORMS = {
        "magic_number": MagicNumberForm,
    }
    _FIELD_DEFAULTS = {
        "magic_number": 42,
    }

    class Meta:
        app_label = "auth"  # not needed outside tests


@preferences(namespace="myotherpref")
class MyOtherPreferences:
    FORMS = {
        "magic_number": MagicNumberForm,
    }
    _FIELD_DEFAULTS = {
        "magic_number": 5,
    }

    class Meta:
        app_label = "auth"  # not needed outside tests

    def get_context(self):
        context = super().get_context()
        context["jazzpunk"] = "For Great Justice!"
        return context

    def update_context(self, _):
        return {"foobar": "xux"}
