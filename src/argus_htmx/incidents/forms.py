from django import forms

class AckForm(forms.Form):
    description = forms.CharField()
    expiration = forms.DateTimeField(required=False)

