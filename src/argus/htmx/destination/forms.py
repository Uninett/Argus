from django import forms
from django.forms import ModelForm

from argus.notificationprofile.models import DestinationConfig, Media
from argus.notificationprofile.serializers import RequestDestinationConfigSerializer
from argus.notificationprofile.media import api_safely_get_medium_object


class DestinationFormCreate(ModelForm):
    settings = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        # Serializer request the request object
        self.request = kwargs.pop("request", None)
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
        settings_key = _get_settings_key_for_media(self.cleaned_data["media"])
        # Convert settings value (e.g. email address) to be compatible with JSONField
        self.cleaned_data["settings"] = {settings_key: self.cleaned_data["settings"]}
        self._init_serializer()
        return self._validate_serializer()

    def save(self):
        # self.serializer should be initiated and validated in clean() before save() is called
        self.serializer.save(user=self.request.user)

    def _init_serializer(self):
        serializer = RequestDestinationConfigSerializer(
            data={
                "media": self.cleaned_data["media"],
                "label": self.cleaned_data.get("label", ""),
                "settings": self.cleaned_data["settings"],
            },
            context={"request": self.request},
        )
        self.serializer = serializer

    def _validate_serializer(self):
        media = self.cleaned_data["media"]
        settings_key = _get_settings_key_for_media(media)

        # Add error messages from serializer to form
        if not self.serializer.is_valid():
            for error_name, error_detail in self.serializer.errors.items():
                if error_name in ["media", "label", settings_key]:
                    if error_name == settings_key:
                        error_name = "settings"
                    self.add_error(error_name, error_detail)
                    # Serializer might add more data to the JSON dict
                    if settings := self.serializer.data.get("settings"):
                        self.cleaned_data["settings"] = settings
        else:
            # Serializer might add more data to the JSON dict
            if settings := self.serializer.validated_data.get("settings"):
                self.cleaned_data["settings"] = settings

        if label := self.cleaned_data.get("label"):
            destination_filter = DestinationConfig.objects.filter(label=label, media=media)
            if self.instance:
                destination_filter = destination_filter.exclude(pk=self.instance.pk)
            if destination_filter.exists():
                self.add_error("label", "Name must be unique per media")

        return self.cleaned_data


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

    def _init_serializer(self):
        # self.instance is modified in __init__,
        # so get unmodified version here for the serializer
        destination = DestinationConfig.objects.get(pk=self.instance.pk)
        settings_key = _get_settings_key_for_media(destination.media)
        data = {}

        if "label" in self.cleaned_data:
            label = self.cleaned_data["label"]
            if label != destination.label:
                data["label"] = label

        settings = self.cleaned_data["settings"]
        if settings.get(settings_key) != destination.settings.get(settings_key):
            data["settings"] = settings

        self.serializer = RequestDestinationConfigSerializer(
            destination,
            data=data,
            context={"request": self.request},
            partial=True,
        )


def _get_settings_key_for_media(media: Media) -> str:
    """Returns the required settings key for the given media,
    e.g. "email_address", "phone_number"
    """
    medium = api_safely_get_medium_object(media.slug)
    return medium.MEDIA_JSON_SCHEMA["required"][0]
