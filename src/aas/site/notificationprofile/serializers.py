from rest_framework import fields, serializers

from .fields import FilterManyToManyField, TimeSlotGroupForeignKeyField
from .models import Filter, NotificationProfile, TimeSlot, TimeSlotGroup


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['day', 'start', 'end']

    def validate(self, attrs):
        if attrs['start'] >= attrs['end']:
            raise serializers.ValidationError("Start time must be before end time.")
        return attrs


class TimeSlotGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlotGroup
        fields = ['pk', 'name', 'time_slots']
        read_only_fields = ['pk']

    time_slots = TimeSlotSerializer(many=True)

    def create(self, validated_data):
        time_slots_data = validated_data.pop('time_slots')
        time_slot_group = TimeSlotGroup.objects.create(**validated_data)
        for time_slot_data in time_slots_data:
            TimeSlot.objects.create(group=time_slot_group, **time_slot_data)

        return time_slot_group

    def update(self, time_slot_group, validated_data):
        time_slots_data = validated_data.pop('time_slots')

        # Replace existing time slots with posted time slots
        time_slot_group.time_slots.all().delete()
        for time_slot_data in time_slots_data:
            TimeSlot.objects.create(group=time_slot_group, **time_slot_data)

        return time_slot_group


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ['pk', 'name', 'filter_string']
        read_only_fields = ['pk']


class NotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProfile
        fields = ['pk', 'time_slot_group', 'filters', 'media', 'active']
        read_only_fields = ['pk']

    time_slot_group = TimeSlotGroupForeignKeyField()
    filters = FilterManyToManyField(many=True)
    media = fields.MultipleChoiceField(choices=NotificationProfile.MEDIA_CHOICES)
