from django import forms
from django.forms import modelform_factory

from argus.auth.models import User
from .models import SourceSystem


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
