from django.db import IntegrityError
from rest_framework import fields, serializers

from .fields import FilterManyToManyField, TimeSlotForeignKeyField
from .models import Filter, NotificationProfile, TimeInterval, TimeSlot
from .validators import FilterStringValidator


class TimeIntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeInterval
        fields = ["day", "start", "end"]

    def validate(self, attrs):
        if attrs["start"] >= attrs["end"]:
            raise serializers.ValidationError("Start time must be before end time.")
        return attrs


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ["pk", "name", "time_intervals"]
        read_only_fields = ["pk"]

    time_intervals = TimeIntervalSerializer(many=True)

    def create(self, validated_data):
        time_intervals_data = validated_data.pop("time_intervals")
        try:
            time_slot = TimeSlot.objects.create(**validated_data)
        except IntegrityError as e:
            name = validated_data["name"]
            if TimeSlot.objects.filter(name=name).exists():
                raise serializers.ValidationError(
                    f"TimeSlot with the name '{name}' already exists for the user {validated_data['user']}."
                )
            else:
                raise e

        for time_interval_data in time_intervals_data:
            TimeInterval.objects.create(time_slot=time_slot, **time_interval_data)

        return time_slot

    def update(self, time_slot: TimeSlot, validated_data):
        time_intervals_data = validated_data.pop("time_intervals")

        time_slot.name = validated_data["name"]
        time_slot.save()

        # Replace existing time intervals with posted time intervals
        time_slot.time_intervals.all().delete()
        for time_interval_data in time_intervals_data:
            TimeInterval.objects.create(time_slot=time_slot, **time_interval_data)

        return time_slot


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ["pk", "name", "filter_string"]
        read_only_fields = ["pk"]

    filter_string = serializers.CharField(validators=[FilterStringValidator()])


class NotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProfile
        fields = ["pk", "time_slot", "filters", "media", "active"]
        read_only_fields = ["pk"]

    time_slot = TimeSlotForeignKeyField()
    filters = FilterManyToManyField(many=True)
    media = fields.MultipleChoiceField(choices=NotificationProfile.MEDIA_CHOICES)

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            time_slot_pk = validated_data["time_slot"].pk
            if NotificationProfile.objects.filter(pk=time_slot_pk).exists():
                raise serializers.ValidationError(
                    f"NotificationProfile with TimeSlot with pk={time_slot_pk} already exists."
                )
            else:
                raise e
