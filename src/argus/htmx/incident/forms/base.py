from typing import Any, Optional
from urllib.parse import urlencode

from django import forms
from django.http import QueryDict

from argus.auth.utils import get_or_update_preference, get_preference


class IncidentListForm(forms.Form):
    fieldname: str
    field_initial: Any
    widget_classes: str = ""
    widget_template_name: Optional[str] = None
    lookup: Optional[str] = None  # used by filter method
    placeholder: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.widget_template_name:
            self.fields[self.fieldname].widget.template_name = self.widget_template_name
        self.fields[self.fieldname].widget.attrs["class"] = self.widget_classes
        self.fields[self.fieldname].widget.attrs["placeholder"] = self.placeholder

    def get_clean_value(self, request):
        value = self.get_initial_value(request)
        if self.is_valid():
            value = self.cleaned_data[self.fieldname]
        return value

    def get_querydict_for_value(self, request):
        data = {self.fieldname: self.get_clean_value(request)}
        return QueryDict(urlencode(data, doseq=True))

    def filter(self, queryset, request):
        return queryset

    @classmethod
    def _get_initial_preference_value(cls, request, namespace):
        return get_preference(request, namespace, cls.fieldname) or cls.field_initial

    @classmethod
    def _get_initial_session_value(cls, request):
        return request.session.get(cls.fieldname, cls.field_initial) or cls.field_initial

    @classmethod
    def get_initial_value(cls, request):
        return cls.field_initial

    @classmethod
    def get_initial(cls, request):
        return {cls.fieldname: cls.get_initial_value(request)}

    def _store_preference(self, request, namespace):
        _, success = get_or_update_preference(
            request,
            self.get_querydict_for_value(request),
            namespace,
            self.fieldname,
        )
        return success

    def _store_in_session(self, request):
        if self.is_valid():
            value = self.get_clean_value(request)
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


class SearchMixin:
    def filter(self, queryset, request):
        _input = self.get_clean_value(request)
        if _input:
            queryset = queryset.filter(**{self.lookup: _input})
        return queryset


class HasTextSearchMixin:
    def filter(self, queryset, request):
        _input = self.get_clean_value(request)
        if _input == "yes":
            queryset = queryset.exclude(**{self.lookup: ""})
        elif _input == "no":
            queryset = queryset.filter(**{self.lookup: ""})
        return queryset
