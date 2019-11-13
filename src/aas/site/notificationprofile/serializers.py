from django.db import IntegrityError
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
        try:
            time_slot_group = TimeSlotGroup.objects.create(**validated_data)
        except IntegrityError as e:
            name = validated_data['name']
            if TimeSlotGroup.objects.filter(name=name).exists():
                raise serializers.ValidationError(f"TimeSlotGroup with the name '{name}' already exists for the user {validated_data['user']}.")
            else:
                raise e

        for time_slot_data in time_slots_data:
            TimeSlot.objects.create(group=time_slot_group, **time_slot_data)

        return time_slot_group

    def update(self, time_slot_group: TimeSlotGroup, validated_data):
        time_slots_data = validated_data.pop('time_slots')

        time_slot_group.name = validated_data['name']
        time_slot_group.save()

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

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            time_slot_group_pk = validated_data['time_slot_group'].pk
            if NotificationProfile.objects.filter(pk=time_slot_group_pk).exists():
                raise serializers.ValidationError(f"NotificationProfile with TimeSlotGroup with pk {time_slot_group_pk} already exists.")
            else:
                raise e
