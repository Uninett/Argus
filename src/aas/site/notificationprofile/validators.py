import json
from typing import Union

from rest_framework import serializers

from .models import Filter


class FilterStringValidator:
    def __call__(self, value: Union[str, dict]):
        if type(value) is str:
            try:
                json_dict = json.loads(value)
            except json.decoder.JSONDecodeError as e:
                raise serializers.ValidationError(e)
        elif type(value) is dict:
            json_dict = value
        else:
            raise serializers.ValidationError(f"The type must be either str or dict, not {type(value)}.")

        for filter_field_name in Filter.FILTER_STRING_FIELDS:
            self._get_filter_field(filter_field_name, json_dict)
        return value

    @staticmethod
    def _get_filter_field(filter_field_name: str, json_dict: dict):
        try:
            return json_dict[filter_field_name]
        except KeyError:
            raise serializers.ValidationError(f"Can't find any '{filter_field_name}' field.")
