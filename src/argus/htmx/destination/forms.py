from django import forms
from django.forms import ModelForm

from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.media import api_safely_get_medium_object


class DestinationFormCreate(ModelForm):
    settings = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        # Serializer needs the request object
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = DestinationConfig
        fields = ["label", "media", "settings"]
        labels = {
            "label": "Name",
        }
        widgets = {
            "media": forms.Select(attrs={"class": "select input-bordered w-full max-w-xs"}),
        }

    def clean(self):
        super().clean()
        media = self.cleaned_data["media"]
        medium = api_safely_get_medium_object(media.slug)()
        settings_key = _get_settings_key_for_media(self.cleaned_data["media"])
        # Convert settings value (e.g. email address) to be compatible with JSONField
        self.cleaned_data["settings"] = {settings_key: self.cleaned_data["settings"]}

        # Update form needs to set instance.settings back to the json dict form before validating

        form = self._validate(medium)
        return form.cleaned_data

    def save(self):
        # Manual save to include user since the form itself does not have a user field
        new_destination = DestinationConfig(
            user=self.cleaned_data["user"],
            media=self.cleaned_data["media"],
            label=self.cleaned_data.get("label", ""),
            settings=self.cleaned_data["settings"],
        )
        new_destination.save()

    def _validate(self, medium):
        return medium.validate(data=self.cleaned_data, user=self.user)


class DestinationFormUpdate(DestinationFormCreate):
    def __init__(self, *args, **kwargs):
        if instance := kwargs.get("instance"):
            settings_key = _get_settings_key_for_media(instance.media)
            # Extract settings value (email address etc.) from JSONField
            instance.settings = instance.settings.get(settings_key)
        super().__init__(*args, **kwargs)

    class Meta:
        model = DestinationConfig
        fields = ["label", "media", "settings"]
        labels = {
            "label": "Name",
        }
        widgets = {
            "media": forms.HiddenInput(),
        }

    def save(self):
        self.instance.settings = self.cleaned_data["settings"]
        self.instance.label = self.cleaned_data.get("label", "")
        self.instance.save()

    def _validate(self, medium):
        # raise ValueError(str(self.cleaned_data["media"]) == self.instance.media.slug)
        return medium.validate(data=self.cleaned_data, user=self.user, instance=self.instance)


def _get_settings_key_for_media(media: Media) -> str:
    """Returns the required settings key for the given media,
    e.g. "email_address", "phone_number"
    """
    medium = api_safely_get_medium_object(media.slug)
    return medium.MEDIA_JSON_SCHEMA["required"][0]
