from django import forms

from argus.incident.forms import AddSourceSystemForm
from argus.incident.models import SourceSystem, SourceSystemType


class CreateSourceSystemForm(AddSourceSystemForm):
    class Meta(AddSourceSystemForm.Meta):
        widgets = {
            "name": forms.TextInput,
            "base_url": forms.TextInput,
        }


class UpdateSourceSystemForm(forms.ModelForm):
    class Meta:
        model = SourceSystem
        fields = ["name", "base_url"]
        widgets = {
            "name": forms.TextInput,
            "base_url": forms.TextInput,
        }


class AddSourceSystemTypeForm(forms.ModelForm):
    class Meta:
        model = SourceSystemType
        fields = ["name"]
        widgets = {
            "name": forms.TextInput,
        }
