import random
from typing import Tuple, Type, Union

from django.db import IntegrityError, models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Alert, NetworkSystem, Object, ObjectType, ParentObject, ProblemType
from .utils import MappingUtils


# TODO: move to tests
def validate_field_mappings(model: Type[models.Model], field_mappings: dict):
    for field_name, field_value_getter in field_mappings.items():
        if not hasattr(model, field_name):
            raise ValueError(f"{model} has no attribute '{field_name}'")

        if type(field_value_getter) is PassthroughField:
            if model._meta.get_field(field_name).is_relation:
                raise ValueError(f"The field {field_name} is a relational field and cannot be paired up with a PassthroughField.")
        elif type(field_value_getter) is ForeignKeyField:
            if not model._meta.get_field(field_name).is_relation:
                raise ValueError(f"The field {field_name} is not a relational field and cannot be paired up with a ForeignKeyField.")
        elif field_value_getter is not None:
            raise ValueError("The type of the values of the dicts must either be an instance of FieldValueGetter or None,"
                             f" not {type(field_value_getter)}.")


class NestedKey:
    def __init__(self, key: str, *, super_keys: Tuple[str, ...] = ()):
        self.super_keys = super_keys + (key,)

    def __getitem__(self, key):
        return NestedKey(key, super_keys=self.super_keys)

    def get_value_from(self, nested_dict: dict):
        value = nested_dict
        for key in self.super_keys:
            value = value[key]
        return value


class Choose:
    def __init__(self, arg: dict, if_value_of: Union[str, NestedKey], is_one_of: tuple, else_arg: dict):
        self.arg = arg
        self.if_value_of = if_value_of
        self.is_one_of = is_one_of
        self.else_arg = else_arg

    def based_on(self, dict_: dict):
        if type(self.if_value_of) is NestedKey:
            value = self.if_value_of.get_value_from(dict_)
        else:
            value = dict_[self.if_value_of]

        return self.arg if value in self.is_one_of else self.else_arg


class FieldValueGetter:
    def prepare(self, field_name: str, model_for_field: Type[models.Model]):
        """
        Must be called before setting any fields.
        """
        pass

    def get_value_from_dict(self, json_dict: dict):
        pass


class PassthroughField(FieldValueGetter):
    def __init__(self, key_name: Union[str, NestedKey]):
        self.key_name = key_name
        self.none_value = None

    def prepare(self, field_name, model_for_field):
        field = model_for_field._meta.get_field(field_name)
        if isinstance(field, (models.CharField, models.TextField)) and not field.null:
            self.none_value = ""

    def get_value_from_dict(self, json_dict):
        if type(self.key_name) is NestedKey:
            return self.key_name.get_value_from(json_dict)
        else:
            return json_dict[self.key_name]


class ForeignKeyField(FieldValueGetter):
    def __init__(self, foreign_model: Type[models.Model], foreign_model_field_mappings: dict):
        MappingUtils.remove_none_mappings(foreign_model_field_mappings)
        MappingUtils.swap_fields_with_field_names(foreign_model_field_mappings)
        validate_field_mappings(foreign_model, foreign_model_field_mappings)

        self.foreign_model = foreign_model
        self.foreign_model_field_mappings = foreign_model_field_mappings

    def prepare(self, field_name, model_for_field):
        MappingUtils.prepare_field_value_getters(self.foreign_model, self.foreign_model_field_mappings)

    def get_value_from_dict(self, json_dict):
        foreign_model_obj_kwargs = {
            field_name: field_value_getter.get_value_from_dict(json_dict)
            for field_name, field_value_getter in self.foreign_model_field_mappings.items()
        }
        foreign_model_obj, _created = self.foreign_model.objects.get_or_create(**foreign_model_obj_kwargs)
        return foreign_model_obj


class FieldMapping:
    def __init__(self, network_system_type: str, base_field_mappings: dict, *conditional_field_mappings: Choose):
        all_field_mappings = (
            base_field_mappings,
            *(cf.arg for cf in conditional_field_mappings),
            *(cf.else_arg for cf in conditional_field_mappings),
        )
        for field_mappings in all_field_mappings:
            MappingUtils.remove_none_mappings(field_mappings)
            MappingUtils.swap_fields_with_field_names(field_mappings)
            validate_field_mappings(Alert, field_mappings)
            MappingUtils.prepare_field_value_getters(Alert, field_mappings)

        self.network_system_type = network_system_type
        self.base_field_mappings = base_field_mappings
        self.conditional_field_mappings = conditional_field_mappings

    def create_model_obj_from_json(self, json_dict: dict):
        field_mappings = dict(self.base_field_mappings)  # copy dict
        for choice in self.conditional_field_mappings:
            field_mappings.update(choice.based_on(json_dict))

        alert_kwargs = {
            field_name: field_value_getter.get_value_from_dict(json_dict)
            for field_name, field_value_getter in field_mappings.items()
        }

        # TODO: remove once source is saved from posted alerts
        alert_kwargs['source'] = random.choice(NetworkSystem.objects.filter(type=self.network_system_type))

        try:
            alert = Alert.objects.create(**alert_kwargs)
        except IntegrityError as e:
            alert_id = alert_kwargs['alert_id']
            if Alert.objects.filter(alert_id=alert_id).exists():
                raise ValidationError(f"Alert with the alert_id '{alert_id}' already exists for"
                                      f" the NetworkSystem '{alert_kwargs['source']}'.")
            else:
                raise e

        # Re-fetch the alert to get parsed field values (e.g. replace timestamp str with datetime)
        alert = Alert.objects.get(pk=alert.pk)
        return alert


NAV_FIELD_MAPPING = FieldMapping(
    NetworkSystem.NAV,
    {
        Alert.timestamp:    PassthroughField('time'),
        Alert.source:       None,  # TODO: save source from posted alert
        Alert.alert_id:     PassthroughField('history'),
        Alert.details_url:  PassthroughField('alert_details_url'),
        Alert.problem_type: ForeignKeyField(ProblemType,
                                            {
                                                ProblemType.name:        PassthroughField(NestedKey('alert_type')['name']),
                                                ProblemType.description: PassthroughField(NestedKey('alert_type')['description']),
                                            }),
        Alert.description:  PassthroughField('message'),
        # None:               ('on_maintenance',
        #                      'acknowledgement',
        #                      'event_history_url',
        #                      'device_groups',
        #                      'event_type',
        #                      'value',
        #                      'severity',
        #                      'source',
        #                      'device'),
    },
    Choose(
        arg={
            Alert.object:        ForeignKeyField(Object,
                                                 {
                                                     Object.name:      PassthroughField('subject'),
                                                     Object.object_id: PassthroughField('netbox'),
                                                     Object.url:       PassthroughField('subject_url'),
                                                     Object.type:      ForeignKeyField(ObjectType,
                                                                                       {
                                                                                           ObjectType.name: PassthroughField('subject_type'),
                                                                                       }),
                                                 }),
            Alert.parent_object: None,
        },
        if_value_of='subid', is_one_of=("", None),
        else_arg={
            Alert.object:        ForeignKeyField(Object,
                                                 {
                                                     Object.name:      PassthroughField('subject'),
                                                     Object.object_id: PassthroughField('subid'),
                                                     Object.url:       PassthroughField('subject_url'),
                                                     Object.type:      ForeignKeyField(ObjectType,
                                                                                       {
                                                                                           ObjectType.name: PassthroughField('subject_type'),
                                                                                       }),
                                                 }),
            Alert.parent_object: ForeignKeyField(ParentObject,
                                                 {
                                                     ParentObject.parentobject_id: PassthroughField('netbox'),
                                                     ParentObject.url:             PassthroughField('netbox_history_url'),
                                                 }),
        }
    )
)

SOURCE_MAPPING_DICT = {
    NetworkSystem.NAV:    NAV_FIELD_MAPPING,
    NetworkSystem.ZABBIX: None,
}


def create_alert_from_json(json_dict: dict, alert_source_type: str):
    try:
        mapping = SOURCE_MAPPING_DICT[alert_source_type]
    except KeyError:
        raise serializers.ValidationError(f"Invalid network system type '{alert_source_type}'.")

    return mapping.create_model_obj_from_json(json_dict)
