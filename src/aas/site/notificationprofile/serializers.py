from rest_framework import serializers

<<<<<<< HEAD
from .models import NotificationProfile, TimeSlot, TimeSlotGroup


class TimeSlotGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlotGroup
        fields = ['pk', 'name', 'time_slots']
        read_only_fields = ['pk']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['time_slots'] = TimeSlotSerializer(instance.time_slots, many=True).data
        return representation


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['pk', 'day', 'start', 'end', 'group']
        read_only_fields = ['pk']
=======
from .models import NotificationProfile, Filter
>>>>>>> origin/dev


class NotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProfile
        fields = ['pk', 'time_slot_group', 'media']
        read_only_fields = ['pk']


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ['user', 'name', 'filter']
        read_only_fields = ["user"]
