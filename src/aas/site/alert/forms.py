from django import forms


class AlertJsonForm(forms.Form):
    json = forms.CharField(widget=forms.Textarea)
