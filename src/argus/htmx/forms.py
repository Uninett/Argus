from django import forms
from django.core.exceptions import ValidationError


__all__ = ["StyleGuideForm"]


class RequiredCheckboxInput(forms.CheckboxInput):
    template_name = "django/forms/widgets/required_checkbox.html"


class RequiredRadioInput(forms.CheckboxInput):
    template_name = "django/forms/widgets/required_radio.html"


class ArgusFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""


class StyleGuideForm(ArgusFormMixin, forms.Form):
    ERROR_INPUT = "MXZ"
    _choices = ("S", "Medium", "Loooooooong", "Multi word long choice")
    CHOICES = tuple(enumerate(_choices, 1))

    # field variations:
    required = forms.CharField(required=True)
    required_checkbox = forms.BooleanField(required=True, widget=RequiredCheckboxInput)
    required_radio = forms.BooleanField(required=True, widget=RequiredRadioInput)
    help_text = forms.CharField(
        required=False, help_text="This is the help text for a specific field, should always be shown"
    )
    error = forms.CharField(required=True)

    # field types:
    input_ = forms.CharField(label="Input", required=False)
    password = forms.Field(required=False, widget=forms.PasswordInput)
    number = forms.IntegerField(required=False)
    date = forms.DateField(required=False)
    datetime = forms.DateTimeField(required=False)
    time = forms.TimeField(required=False)
    email = forms.EmailField(required=False)
    url = forms.URLField(required=False)
    checkbox = forms.BooleanField(required=False)
    select = forms.ChoiceField(required=False, choices=CHOICES)
    checkbox_select = forms.ChoiceField(
        required=False,
        choices=CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    radio_select = forms.ChoiceField(
        required=False,
        choices=CHOICES,
        widget=forms.RadioSelect,
    )

    # special field types:
    # level as range
    # typeahead
    # ..

    def clean_error(self):
        input = self.cleaned_data.get("error", "")
        if input != self.ERROR_INPUT:
            raise ValidationError(
                'This field only accepts "%(correct)s" as a value',
                params={"correct": self.ERROR_INPUT},
                code="invalid",
            )
        return input

    def clean(self):
        cleaned_data = super().clean()
        if not (cleaned_data.get("error", None) and cleaned_data.get("required", None)):
            raise ValidationError(
                'Both of the fields "required" and "error" needs to be filled and valid',
                code="invalid",
            )
