from typing import Type, Union

from django.db import models
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.db.models.query_utils import DeferredAttribute


class MappingUtils:
    @staticmethod
    def remove_none_mappings(field_mappings: dict):
        for field, field_value_getter in dict(field_mappings).items():  # copy dict
            if field is None or field_value_getter is None:
                field_mappings.pop(field)

    @staticmethod
    def swap_fields_with_field_names(field_mappings: dict):
        for field in set(field_mappings.keys()):  # copy set
            field_value_getter = field_mappings.pop(field)
            field_name = MappingUtils._get_field_name(field)
            field_mappings[field_name] = field_value_getter

    @staticmethod
    def _get_field_name(field: Union[DeferredAttribute, ForwardManyToOneDescriptor]):
        if type(field) in {DeferredAttribute, ForwardManyToOneDescriptor}:
            return field.field.name
        else:
            raise ValueError(f"Unknown field type {type(field)}.")

    @staticmethod
    def prepare_field_value_getters(model: Type[models.Model], field_mappings: dict):
        for field_name, field_value_getter in field_mappings.items():
            field_value_getter.prepare(field_name, model)
