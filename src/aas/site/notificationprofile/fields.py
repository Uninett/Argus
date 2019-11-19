from rest_framework.relations import PrimaryKeyRelatedField

from . import serializers


class TimeSlotForeignKeyField(PrimaryKeyRelatedField):
    def get_queryset(self):
        return self.context['request'].user.time_slots.all()

    def use_pk_only_optimization(self):
        # Disable using a mock object to wrap only the pk of a TimeSlot when running `to_representation()`
        return False

    def to_representation(self, value):
        return serializers.TimeSlotSerializer(value).data


class FilterManyToManyField(PrimaryKeyRelatedField):
    def get_queryset(self):
        return self.context['request'].user.filters.all()

    def use_pk_only_optimization(self):
        # Disable using a mock object to wrap only the pk of a Filter when running `to_representation()`
        return False

    def to_representation(self, value):
        return serializers.FilterSerializer(value).data
