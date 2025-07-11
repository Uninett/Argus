from django import forms


class IncidentListForm(forms.Form):
    def get_clean_value(self):
        value = self.field_initial
        if self.is_bound and self.is_valid():
            value = self.cleaned_data[self.fieldname]
        return value

    def filter(self, queryset):
        return queryset
