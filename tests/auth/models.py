from django import forms

from argus.auth.models import PreferenceField, preferences


class MagicNumberForm(forms.Form):
    magic_number = forms.IntegerField()


@preferences(namespace="mypref")
class MyPreferences:
    FIELDS = {"magic_number": PreferenceField(form=MagicNumberForm, default=42)}

    class Meta:
        app_label = "auth"  # not needed outside tests


@preferences(namespace="myotherpref")
class MyOtherPreferences:
    FIELDS = {"magic_number": PreferenceField(form=MagicNumberForm, default=5)}

    class Meta:
        app_label = "auth"  # not needed outside tests

    def get_context(self):
        context = super().get_context()
        context["jazzpunk"] = "For Great Justice!"
        return context

    def update_context(self, _):
        return {"foobar": "xux"}
