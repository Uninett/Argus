from django import forms
from django.forms import fields

import rest_framework.fields as rest_framework_fields

import django_psycopg_infinity.utils as utils
from django_psycopg_infinity.fields import DateTimeInfinityField  # noqa: F401 — re-exported for backwards compatibility
from .validators import validate_key_value


class SplitDateTimeInfinityField(forms.SplitDateTimeField):
    empty_values = forms.SplitDateTimeField.empty_values + [False]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields = (*self.fields, fields.BooleanField(required=False))

    def compress(self, data_list: list):
        if not data_list:
            return None

        date, time, infinity_checked = data_list
        if infinity_checked:
            return utils.INFINITY_REPR
        return super().compress([date, time])


def _get_default_error_messages_for_datetime_infinity_serializer_field():
    messages = rest_framework_fields.DateTimeField.default_error_messages
    invalid_message = messages["invalid"]
    messages["invalid"] = f"{invalid_message.rstrip('.')}, or '{utils.INFINITY_REPR}'."
    return messages


class DateTimeInfinitySerializerField(rest_framework_fields.DateTimeField):
    default_error_messages = _get_default_error_messages_for_datetime_infinity_serializer_field()

    def to_internal_value(self, value):
        return utils.get_infinity_time(value) or super().to_internal_value(value)

    def to_representation(self, value):
        return utils.get_infinity_repr(value, str_repr=True) or super().to_representation(value)


class KeyValueField(forms.CharField):
    default_validators = [validate_key_value]
