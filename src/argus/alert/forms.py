from django import forms
from django.forms import modelform_factory

from argus.auth.models import User
from .models import AlertSource


class AlertJsonForm(forms.Form):
    json = forms.CharField(widget=forms.Textarea)


class AddAlertSourceForm(forms.ModelForm):
    username = forms.CharField(
        label="Username for alert source's system user",
    )

    class Meta:
        model = AlertSource
        exclude = ["user"]

    def clean_username(self):
        username = self.cleaned_data["username"]
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

        instance: AlertSource = super().save(False)

        user = User.objects.create(username=self.cleaned_data["username"])
        instance.user = user
        if commit:
            instance.save()

        return instance
