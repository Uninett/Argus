from django import forms

from argus.incident.forms import AddSourceSystemForm
from argus.incident.models import SourceSystem, SourceSystemType


class CreateSourceSystemForm(AddSourceSystemForm):
    class Meta(AddSourceSystemForm.Meta):
        widgets = {
            "name": forms.TextInput,
            "base_url": forms.TextInput,
            "heartbeat_frequency": forms.TextInput(attrs={"placeholder": "00:01:00"}),
        }


class UpdateSourceSystemForm(forms.ModelForm):
    class Meta:
        model = SourceSystem
        fields = ["name", "type", "base_url", "heartbeat_frequency"]
        widgets = {
            "name": forms.TextInput,
            "base_url": forms.TextInput,
            "heartbeat_frequency": forms.TextInput(attrs={"placeholder": "00:01:00"}),
        }


class AddSourceSystemTypeForm(forms.ModelForm):
    class Meta:
        model = SourceSystemType
        fields = ["name"]
        widgets = {
            "name": forms.TextInput,
        }
