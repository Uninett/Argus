from django import forms
from django.core.exceptions import ValidationError


__all__ = ["StyleGuideForm"]


class StyleGuideForm(forms.Form):
    INITIAL_DATA = "Field with initial data"
    ERROR_INPUT = "MXZ"
    _choices = ("Choice 1", "Choice 2", "Choice 3")
    CHOICES = zip(_choices, _choices)

    # field variations:
    required = forms.CharField(required=True)
    initial = forms.CharField(required=False, initial=INITIAL_DATA)
    help_text = forms.CharField(
        required=False, help_text="This is the help text for a specific field, should always be shown"
    )
    error = forms.CharField(required=True)

    # field types:
    input = forms.CharField(required=False)
    password = forms.Field(required=False, widget=forms.PasswordInput)
    number = forms.IntegerField(required=False)
    date = forms.DateField(required=False)
    datetime = forms.DateTimeField(required=False)
    time = forms.TimeField(required=False)
    email = forms.EmailField(required=False)
    url = forms.URLField(required=False)
    checkbox = forms.BooleanField(required=False)
    select = forms.ChoiceField(required=False, choices=CHOICES)

    # special field types:
    # level as range
    # typeahead
    # ..

    def clean_initial(self):
        return self.INITIAL_DATA

    def clean_error(self):
        input = self.cleaned_data.get("error", "")
        if input != self.ERROR_INPUT:
            raise ValidationError(
                'This field only accepts "%(correct)s" as a value',
                params={"correct": self.ERROR_INPUT},
                code="invalid",
            )
        return input
