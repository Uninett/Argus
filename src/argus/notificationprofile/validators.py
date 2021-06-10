import json
from typing import Union

from rest_framework import serializers

from .constants import DEPRECATED_FILTER_NAMES
from .primitive_serializers import FilterBlobSerializer


def validate_filter_string(value: Union[str, dict]):
    if isinstance(value, str):
        try:
            json_dict = json.loads(value)
        except json.decoder.JSONDecodeError as e:
            raise serializers.ValidationError(e)
    elif isinstance(value, dict):
        json_dict = value
    else:
        raise serializers.ValidationError(f"The type must be either str or dict, not {type(value)}.", "format_error")

    errors = []
    keys_in_filterstring = set(json_dict.keys())
    filter_names = set(DEPRECATED_FILTER_NAMES)
    found = filter_names.intersection(keys_in_filterstring)
    if not found:
        errors.append(serializers.ValidationError("No known fieldnames in filterstring.", "none_found"))
    missing = filter_names.difference(keys_in_filterstring)
    if missing:
        pp_missing = ", ".join(missing)
        errors.append(serializers.ValidationError(f"Filterstring is missing fieldname(s): {pp_missing}", "missing"))
    unknown = keys_in_filterstring.difference(filter_names)
    if unknown:
        pp_unknown = ", ".join(unknown)
        errors.append(serializers.ValidationError(f"Unknown fieldname(s) in filterstring: {pp_unknown}", "unknown"))
    if errors:
        raise serializers.ValidationError(errors)


def validate_jsonfilter(value: dict):
    if not isinstance(value, dict):
        raise serializers.ValidationError("Filter is not a dict")
    if not value:
        return True
    serializer = FilterBlobSerializer(data=value)
    if serializer.is_valid():
        return True
    raise serializers.ValidationError("Filter is not valid")
