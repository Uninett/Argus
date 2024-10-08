from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import modelform_factory

from .constants import Level
from .models import Incident, SourceSystem, Tag

User = get_user_model()


class AddSourceSystemForm(forms.ModelForm):
    username = forms.CharField(
        required=False,
        label="Username for the source system's system user",
        help_text="Defaults to the provided name of the source system.",
    )

    class Meta:
        model = SourceSystem
        exclude = ["user"]

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not username:
            username = self.cleaned_data["name"]
            # Update the form's bound data to show the user which value was used while validating
            # - in case the username causes errors
            bound_data = self.data.copy()
            bound_data["username"] = username
            self.data = bound_data

        UserForm = modelform_factory(User, fields=["username"])
        user_form = UserForm({"username": username})
        if not user_form.is_valid():
            raise forms.ValidationError(
                [
                    f"{field}: {list(message) if len(message) > 1 else message[0]}"
                    for field, message in user_form.errors.items()
                ]
            )
        return username

    def save(self, commit=True):
        if self.errors:
            return super().save(commit)

        instance: SourceSystem = super().save(False)

        user = User.objects.create(username=self.cleaned_data["username"])
        instance.user = user
        if commit:
            instance.save()

        return instance


class FakeIncidentForm(forms.ModelForm):
    level = forms.TypedChoiceField(
        choices=[("", "")] + [(str(level), str(level)) for level in Level.values],
        coerce=int,
    )
    stateful = forms.BooleanField(
        initial=True, help_text="Stateful = incident with start and end, not stateful = single point in time incident"
    )
    tags = forms.CharField(help_text="Comma separated of form key=value")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Incident
        fields = [
            "stateful",
            "description",
            "level",
            "tags",
            "metadata",
        ]

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        if tags:
            tag_list = tags.split(",")
            for tag in tag_list:
                try:
                    Tag.split(tag=tag)
                except (ValueError, ValidationError) as e:
                    raise forms.ValidationError(str(e))
            tags = tag_list
        return tags
