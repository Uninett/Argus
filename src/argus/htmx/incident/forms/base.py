from typing import Any
from urllib.parse import urlencode

from django import forms
from django.http import QueryDict

from argus.auth.utils import get_or_update_preference


class IncidentListForm(forms.Form):
    fieldname: str
    field_initial: Any

    def get_clean_value(self):
        value = self.field_initial
        if self.is_bound and self.is_valid():
            value = self.cleaned_data[self.fieldname]
        return value

    def get_querydict_for_value(self):
        data = {self.field_name: self.get_clean_value()}
        return QueryDict(urlencode(data, doseq=True))

    def filter(self, queryset):
        return queryset

    def _store_preference(self, request, preference):
        _, success = get_or_update_preference(
            request,
            self.get_querydict_for_value(),
            preference,
            self.fieldname,
        )
        return success

    def _store_in_session(self, request):
        if self.is_valid():
            value = self.get_querydict_for_value()
            request.session[self.fieldname] = value
            return True
        return False

    def store(self, request):
        """Store value of field_name

        ``request`` is used to store preferences or in session, and to add
        messages.

        Returns:

        - ``None`` if not implemented
        - ``True`` if implemented and successfully stored
        - ``False`` if implemented but storing was not possible
        """
        # Use self.get_clean_value() to get value to store
        return None
