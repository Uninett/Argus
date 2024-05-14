from rest_framework import serializers


class CustomMultipleChoiceField(serializers.MultipleChoiceField):
    def to_internal_value(self, value):
        return list(super().to_internal_value(value))
